#!/usr/bin/env python3
"""
Sync server IPs from Terraform output into the Ansible inventory.

Workflow: terraform apply -> this script -> ansible-playbook against the
now-current inventory. Replaces the previous all-manual step of copying
the `ansible_inventory` output and pasting it into hosts.yml by hand.

Deliberately NOT a full inventory regeneration: this only updates the
ansible_host/ansible_port fields of hosts that already exist in the
static inventory file, by matching on the host's NAME (the key Terraform's
ansible_inventory_entry output uses, e.g. "web01"). Everything else in
hosts.yml — group structure, server_name, per-host or per-group vars like
staging's relaxed fail2ban settings — is read and written back completely
untouched. A from-scratch regeneration would risk silently destroying
that hand-curated structure, which isn't sourced from Terraform at all
(e.g. the "monitoring" group in production/hosts.yml has no Terraform
module backing it whatsoever).

Usage:
    python3 scripts/sync-inventory-from-terraform.py production
    python3 scripts/sync-inventory-from-terraform.py staging

Requires: terraform state to already exist for the given environment
(i.e. `terraform apply` has actually been run there) and an
"ansible_inventory" output exposing the vps module's
ansible_inventory_entry output — both environments already have this.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
TERRAFORM_ENV_DIR = REPO_ROOT / "terraform" / "environments"
INVENTORY_DIR = REPO_ROOT / "ansible" / "inventory"


def get_terraform_outputs(env: str) -> dict:
    env_dir = TERRAFORM_ENV_DIR / env
    if not env_dir.is_dir():
        print(f"No such Terraform environment: {env_dir}", file=sys.stderr)
        sys.exit(1)

    try:
        result = subprocess.run(
            ["terraform", "output", "-json"],
            cwd=env_dir, capture_output=True, text=True, check=True,
        )
    except FileNotFoundError:
        print("terraform binary not found on PATH.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"terraform output failed:\n{e.stderr}", file=sys.stderr)
        sys.exit(1)

    return json.loads(result.stdout)


def parse_inventory_entries(outputs: dict) -> dict[str, dict]:
    """
    Finds every output named (or ending in) "ansible_inventory" — each
    one's value is a YAML snippet like:
        web01:
          ansible_host: 1.2.3.4
          ansible_port: 22
    Parses each into {host_name: {ansible_host: ..., ansible_port: ...}}.
    Handles multiple such outputs (e.g. a future environment with more
    than one server) without hardcoding specific output names — current
    environments differ already (production's module is "web01",
    staging's is "staging01", with no consistent naming convention
    between them), so matching by suffix rather than an exact name is
    deliberate, not an oversight.
    """
    entries: dict[str, dict] = {}
    for name, data in outputs.items():
        if not name.endswith("ansible_inventory"):
            continue
        value = data.get("value", "")
        if not value or not isinstance(value, str):
            continue
        try:
            parsed = yaml.safe_load(value)
        except yaml.YAMLError:
            continue
        if isinstance(parsed, dict):
            entries.update(parsed)
    return entries


def update_hosts_in_place(inventory: dict, entries: dict[str, dict]) -> list[str]:
    """Walks all.children.*.hosts.* looking for a host name matching one
    of the Terraform-sourced entries, updating only ansible_host/
    ansible_port on a match. Returns the list of host names actually
    updated, so the caller can report unmatched entries rather than
    silently doing nothing for a typo'd or renamed host."""
    updated = []
    groups = inventory.get("all", {}).get("children", {})
    for _group_name, group in groups.items():
        hosts = group.get("hosts", {}) or {}
        for host_name, host_vars in hosts.items():
            if host_name in entries:
                new_values = entries[host_name]
                host_vars["ansible_host"] = new_values.get("ansible_host", host_vars.get("ansible_host"))
                if "ansible_port" in new_values:
                    host_vars["ansible_port"] = new_values["ansible_port"]
                updated.append(host_name)
    return updated


def main() -> int:
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <environment>", file=sys.stderr)
        return 1
    env = sys.argv[1]

    outputs = get_terraform_outputs(env)
    entries = parse_inventory_entries(outputs)
    if not entries:
        print(f"No ansible_inventory-style outputs found for '{env}' — "
              f"nothing to sync. Has `terraform apply` been run there yet?")
        return 1

    inventory_path = INVENTORY_DIR / env / "hosts.yml"
    if not inventory_path.is_file():
        print(f"No static inventory found at {inventory_path} to update into.", file=sys.stderr)
        return 1

    with open(inventory_path) as f:
        inventory = yaml.safe_load(f)

    updated = update_hosts_in_place(inventory, entries)

    unmatched = set(entries) - set(updated)
    if unmatched:
        print(f"Warning: Terraform output has entries for {sorted(unmatched)} "
              f"that don't match any existing host in {inventory_path} — "
              f"these were NOT added (this script only updates existing "
              f"hosts, see the module docstring for why). Add them to "
              f"hosts.yml by hand once, the usual way, and future syncs "
              f"will keep them updated.")

    if not updated:
        print("No matching hosts updated.")
        return 1

    with open(inventory_path, "w") as f:
        f.write("---\n")
        yaml.safe_dump(inventory, f, default_flow_style=False, sort_keys=False)

    print(f"Updated {', '.join(updated)} in {inventory_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
