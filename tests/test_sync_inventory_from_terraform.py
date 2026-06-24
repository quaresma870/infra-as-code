"""
Tests for scripts/sync-inventory-from-terraform.py.

The script's filename uses hyphens (a CLI tool, not normally imported as a
Python module) so it's loaded here via importlib rather than a plain
import — a standard, valid pattern for testing hyphenated-filename scripts.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "sync-inventory-from-terraform.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("sync_inventory", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def mod():
    return _load_module()


# A real, representative production hosts.yml — including the "monitoring"
# group, which has no Terraform module backing it at all. Any test that
# silently drops or mutates this group has broken the "only touch what
# Terraform actually knows about" guarantee this script exists to provide.
SAMPLE_INVENTORY = {
    "all": {
        "children": {
            "webservers": {
                "hosts": {
                    "web01": {
                        "ansible_host": "1.2.3.4",
                        "ansible_port": 22,
                        "server_name": "web01.example.com",
                    },
                },
                "vars": {"env": "production"},
            },
            "monitoring": {
                "hosts": {
                    "mon01": {"ansible_host": "1.2.3.5", "ansible_port": 22},
                },
            },
        },
        "vars": {"ansible_user": "deploy"},
    },
}


class TestParseInventoryEntries:
    def test_parses_a_single_ansible_inventory_output(self, mod):
        outputs = {
            "web01_ip": {"sensitive": False, "type": "string", "value": "5.6.7.8"},
            "ansible_inventory": {
                "sensitive": False, "type": "string",
                "value": "web01:\n  ansible_host: 5.6.7.8\n  ansible_port: 22\n",
            },
        }
        entries = mod.parse_inventory_entries(outputs)
        assert entries == {"web01": {"ansible_host": "5.6.7.8", "ansible_port": 22}}

    def test_ignores_outputs_not_ending_in_ansible_inventory(self, mod):
        outputs = {
            "web01_ip": {"sensitive": False, "type": "string", "value": "5.6.7.8"},
            "web01_ssh": {"sensitive": False, "type": "string", "value": "ssh ..."},
        }
        assert mod.parse_inventory_entries(outputs) == {}

    def test_matches_by_suffix_not_exact_name(self, mod):
        """production and staging name this output differently in
        practice in this repo's own Terraform (just "ansible_inventory"
        in both cases today, but matched by suffix deliberately so a
        future per-server-prefixed name like "web01_ansible_inventory"
        keeps working without code changes)."""
        outputs = {
            "web01_ansible_inventory": {
                "sensitive": False, "type": "string",
                "value": "web01:\n  ansible_host: 5.6.7.8\n",
            },
        }
        entries = mod.parse_inventory_entries(outputs)
        assert entries == {"web01": {"ansible_host": "5.6.7.8"}}

    def test_handles_multiple_inventory_outputs(self, mod):
        outputs = {
            "web01_ansible_inventory": {
                "sensitive": False, "type": "string",
                "value": "web01:\n  ansible_host: 1.1.1.1\n",
            },
            "web02_ansible_inventory": {
                "sensitive": False, "type": "string",
                "value": "web02:\n  ansible_host: 2.2.2.2\n",
            },
        }
        entries = mod.parse_inventory_entries(outputs)
        assert entries == {
            "web01": {"ansible_host": "1.1.1.1"},
            "web02": {"ansible_host": "2.2.2.2"},
        }

    def test_malformed_yaml_value_is_skipped_not_fatal(self, mod):
        outputs = {
            "ansible_inventory": {
                "sensitive": False, "type": "string",
                "value": "not: valid: yaml: at: all: [[[",
            },
        }
        # Must not raise — a single bad output shouldn't crash the whole sync.
        entries = mod.parse_inventory_entries(outputs)
        assert entries == {}


class TestUpdateHostsInPlace:
    def test_updates_matching_host_in_webservers_group(self, mod):
        inventory = yaml.safe_load(yaml.safe_dump(SAMPLE_INVENTORY))  # deep copy
        updated = mod.update_hosts_in_place(inventory, {"web01": {"ansible_host": "9.9.9.9", "ansible_port": 2222}})
        assert updated == ["web01"]
        host = inventory["all"]["children"]["webservers"]["hosts"]["web01"]
        assert host["ansible_host"] == "9.9.9.9"
        assert host["ansible_port"] == 2222
        assert host["server_name"] == "web01.example.com"  # untouched

    def test_monitoring_group_untouched_when_only_webserver_updated(self, mod):
        """The monitoring group has no Terraform module behind it at all —
        confirms it survives completely unmodified."""
        inventory = yaml.safe_load(yaml.safe_dump(SAMPLE_INVENTORY))
        mod.update_hosts_in_place(inventory, {"web01": {"ansible_host": "9.9.9.9"}})
        assert inventory["all"]["children"]["monitoring"]["hosts"]["mon01"]["ansible_host"] == "1.2.3.5"

    def test_unmatched_entry_is_not_added(self, mod):
        """This script only updates EXISTING hosts by design — a typo'd
        or renamed server name in Terraform output must not silently
        inject a new, unreviewed host into the inventory."""
        inventory = yaml.safe_load(yaml.safe_dump(SAMPLE_INVENTORY))
        updated = mod.update_hosts_in_place(inventory, {"web99-typo": {"ansible_host": "1.1.1.1"}})
        assert updated == []
        assert "web99-typo" not in inventory["all"]["children"]["webservers"]["hosts"]

    def test_group_vars_untouched(self, mod):
        inventory = yaml.safe_load(yaml.safe_dump(SAMPLE_INVENTORY))
        mod.update_hosts_in_place(inventory, {"web01": {"ansible_host": "9.9.9.9"}})
        assert inventory["all"]["vars"]["ansible_user"] == "deploy"
        assert inventory["all"]["children"]["webservers"]["vars"]["env"] == "production"


class TestMainEndToEnd:
    def test_full_sync_against_a_real_file_on_disk(self, mod, tmp_path):
        """End-to-end: writes a real hosts.yml to a temp dir, mocks only
        the terraform-binary-calling function (no real Terraform state
        exists anywhere in this CI/test context — these provision real,
        billed cloud servers), and confirms the file on disk is correctly
        updated afterward."""
        env_dir = tmp_path / "terraform" / "environments" / "test_env"
        env_dir.mkdir(parents=True)
        inv_dir = tmp_path / "ansible" / "inventory" / "test_env"
        inv_dir.mkdir(parents=True)
        inventory_path = inv_dir / "hosts.yml"
        with open(inventory_path, "w") as f:
            yaml.safe_dump(SAMPLE_INVENTORY, f)

        mod.REPO_ROOT = tmp_path
        mod.TERRAFORM_ENV_DIR = tmp_path / "terraform" / "environments"
        mod.INVENTORY_DIR = tmp_path / "ansible" / "inventory"

        mock_outputs = {
            "ansible_inventory": {
                "sensitive": False, "type": "string",
                "value": "web01:\n  ansible_host: 8.8.8.8\n  ansible_port: 2222\n",
            },
        }
        with patch.object(mod, "get_terraform_outputs", return_value=mock_outputs):
            sys.argv = ["sync-inventory-from-terraform.py", "test_env"]
            rc = mod.main()

        assert rc == 0
        with open(inventory_path) as f:
            result = yaml.safe_load(f)
        host = result["all"]["children"]["webservers"]["hosts"]["web01"]
        assert host["ansible_host"] == "8.8.8.8"
        assert host["ansible_port"] == 2222
        assert host["server_name"] == "web01.example.com"
        assert result["all"]["children"]["monitoring"]["hosts"]["mon01"]["ansible_host"] == "1.2.3.5"

    def test_missing_environment_directory_exits_nonzero(self, mod, tmp_path, capsys):
        mod.REPO_ROOT = tmp_path
        mod.TERRAFORM_ENV_DIR = tmp_path / "terraform" / "environments"
        mod.INVENTORY_DIR = tmp_path / "ansible" / "inventory"
        sys.argv = ["sync-inventory-from-terraform.py", "nonexistent_env"]
        with pytest.raises(SystemExit) as exc_info:
            mod.main()
        assert exc_info.value.code != 0

    def test_no_matching_outputs_exits_nonzero_not_silently(self, mod, tmp_path):
        env_dir = tmp_path / "terraform" / "environments" / "test_env"
        env_dir.mkdir(parents=True)
        inv_dir = tmp_path / "ansible" / "inventory" / "test_env"
        inv_dir.mkdir(parents=True)
        with open(inv_dir / "hosts.yml", "w") as f:
            yaml.safe_dump(SAMPLE_INVENTORY, f)

        mod.REPO_ROOT = tmp_path
        mod.TERRAFORM_ENV_DIR = tmp_path / "terraform" / "environments"
        mod.INVENTORY_DIR = tmp_path / "ansible" / "inventory"

        with patch.object(mod, "get_terraform_outputs", return_value={"unrelated_output": {"value": "x"}}):
            sys.argv = ["sync-inventory-from-terraform.py", "test_env"]
            rc = mod.main()
        assert rc != 0
