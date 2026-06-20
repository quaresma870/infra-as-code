# Changelog

All notable changes to this project are documented here. See the
[README](README.md) for current features and usage.

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
