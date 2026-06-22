# Changelog

All notable changes to this project are documented here. See the
[README](README.md) for current features and usage.

### v1.0.4
- fix: **`ansible-lint playbooks/ --profile=basic || true` in CI meant lint could never fail the
  build**, regardless of how many violations existed. Running it without the `|| true` revealed
  **30 real violations** that had been silently accumulating:
  - 10 `partial-become` violations — `become_user` set on a task without an explicit `become: true`
    on that same task, relying on inheriting it from the play level. Currently correct in every
    case (play-level `become: true` was set), but fragile: a later refactor that changes how
    privilege escalation is structured could silently stop applying `become_user` with no error.
    Fixed by adding explicit `become: true` alongside every `become_user:` across `deploy.yml`,
    `rollback.yml`, and the `backup` role.
  - 14 `var-naming` violations — role default variables not prefixed with their role's name
    (`deploy_ssh_keys`, `swap_size_mb`, `ufw_default_incoming`, `ufw_default_outgoing`,
    `ufw_extra_rules`, `node_exporter_version`, `node_exporter_port`, `certbot_email`,
    `certbot_domains`, plus 5 task-internal `register:` variables), risking name collisions across
    roles. Renamed to `common_*`/`firewall_*`/`monitoring_*`/`ssl_*` as appropriate.
    **Backward-compatible for every user-facing default** — each renamed default variable falls
    back to its old, unprefixed name if still set (`common_swap_size_mb: "{{ swap_size_mb |
    default(2048) }}"` etc.), so existing inventories using the old names keep working without
    any changes required. `playbooks/site.yml`'s role-inclusion check for the `ssl` role
    recognises both the old and new variable name. The example inventory
    (`inventory/production/group_vars/all.yml`) was updated to demonstrate the new names going
    forward.
  - 6 `yaml`/`jinja` formatting violations — resolved via `ansible-lint --fix` plus two manual
    fixes that precompute the `ansible_architecture` → Docker/node_exporter release-naming mapping
    once via `set_fact` instead of repeating the same long `replace()` chain inline (which was also
    what pushed those two lines over the line-length limit).
  - With all 30 resolved, the codebase now passes ansible-lint's **`production`** profile (the
    strictest tier), not just the `basic` profile the CI step requires — confirmed by re-running
    the exact command. The `|| true` is now removed from `ci.yml`, so this is actually enforced
    going forward instead of silently ignored.
- fix: **CI never validated the `staging` Terraform environment** — only `production` had a
  `terraform validate` step, despite `staging` having the identical file structure
  (`main.tf`/`outputs.tf`/`variables.tf`/`terraform.tfvars.example`). Manually reviewed `staging`'s
  configuration first (cross-checked every module output it references against the `vps` module's
  actual declared outputs) before adding the missing CI step, confirming there wasn't already a
  broken config hiding behind this blind spot.
- chore: removed leftover empty junk directories from an early shell command that didn't expand
  brace patterns as intended — never tracked in git, purely local clutter.
- noted (not yet fixed): `ansible.builtin.apt_repository` (used in the `docker` role) is deprecated
  as of a recent ansible-core release in favour of `deb822_repository`, scheduled for removal in
  ansible-core 2.25. Not urgent — surfaced by a deprecation warning during this review, worth a
  follow-up migration before that removal lands.

### v1.0.3
- feat: `backup` Ansible role — automated cron backups integrating `compose-stacks/backup.sh` — closes #6
  - Daily backup at 02:00, retention 7 daily / 4 weekly, optional offsite rsync
  - Added to `site.yml` with `--tags backup`
- feat: multi-server inventory example (load balancer + 2 app servers + Redis cache) — closes #7
  - `inventory/production/hosts-multi.yml.example`
  - New `haproxy` role with health-checked round-robin backend
  - New `playbooks/site-multi.yml` — provisions LB + N app servers + shared Redis

### v1.0.2
- docs: remote Terraform state backend options documented (Terraform Cloud + S3) — closes #1
- feat: `ansible/inventory/production/group_vars/vault.yml.example` — Ansible Vault guide — closes #2
- feat: `terraform/environments/staging/` — staging environment (cx11, separate state) — closes #3
- feat: post-deploy health check in `deploy.yml` (60s timeout, fails playbook) — closes #4
- feat: `ansible/playbooks/rollback.yml` — revert to specified image version — closes #5

### v1.0.1
- fix: `requirements.txt` with ansible-core>=2.17, ansible-lint>=24.9.0, yamllint>=1.35.0
- fix: Ansible collections installed before lint in CI
- fix: Terraform `.tf` files rewritten with strict `terraform fmt` alignment
- chore: Ansible upgraded to ansible-core>=2.17 (LTS)
