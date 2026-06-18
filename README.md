# 🏗️ Infra as Code

[![CI](https://github.com/quaresma870/infra-as-code/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/quaresma870/infra-as-code/actions/workflows/ci.yml)
![Ansible](https://img.shields.io/badge/Ansible--core-2.17%2B-EE0000?logo=ansible&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-1.10%2B-7B42BC?logo=terraform&logoColor=white)
![Node.js](https://img.shields.io/badge/GitHub%20Actions-Node.js%2024-brightgreen?logo=nodedotjs&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

Provision and configure production VPS servers from scratch using **Terraform** (Hetzner Cloud) and **Ansible**.

---

## What it does

1. **Terraform** — creates the VPS, firewall rules, SSH key, optional floating IP and extra volume
2. **Ansible bootstrap** — creates deploy user, hardens SSH, installs Python (first run as root)
3. **Ansible site** — applies all roles: common, firewall, fail2ban, docker, nginx, SSL, monitoring

---

## Quick start

### 1. Provision the server (Terraform)

```bash
cd terraform/environments/production
cp terraform.tfvars.example terraform.tfvars
vim terraform.tfvars   # add your Hetzner token and SSH key

terraform init
terraform plan
terraform apply
```

Note the output `web01_ip` — add it to `ansible/inventory/production/hosts.yml`.

### 2. Bootstrap (first run as root)

```bash
cd ansible
ansible-playbook playbooks/bootstrap.yml \
  -i inventory/production \
  --user root \
  --ask-pass \
  --limit web01
```

### 3. Full server setup

```bash
ansible-playbook playbooks/site.yml -i inventory/production --limit web01
```

### 4. Deploy your app

```bash
ansible-playbook playbooks/deploy.yml \
  -i inventory/production \
  --limit web01 \
  --extra-vars "stack=web-basic app_image=ghcr.io/myuser/myapp:v1.2.3"
```

---

## Ansible roles

| Role | What it does |
|------|-------------|
| `common` | Packages, deploy user, SSH hardening, sysctl, swap |
| `firewall` | UFW rules (SSH, HTTP, HTTPS, custom) |
| `fail2ban` | Bans brute-force IPs — SSH, nginx, nginx-botsearch |
| `docker` | Docker CE + Compose plugin, daemon config |
| `nginx` | nginx + rate limiting + security headers + vhost templates |
| `ssl` | Certbot + Let's Encrypt + auto-renewal cron |
| `monitoring` | Prometheus Node Exporter (integrates with compose-stacks/monitoring) |
| `backup` | Automated cron backups via compose-stacks/backup.sh, retention + offsite sync |
| `haproxy` | Load balancer with health-checked round-robin backend (multi-server setups) |

### Tags

Run only specific roles:

```bash
ansible-playbook playbooks/site.yml -i inventory/production --tags docker
ansible-playbook playbooks/site.yml -i inventory/production --tags "nginx,ssl"
ansible-playbook playbooks/site.yml -i inventory/production --tags security
```

### Dry run

```bash
ansible-playbook playbooks/site.yml -i inventory/production --check --diff
```

---

## Terraform module

The `modules/vps` module provisions on Hetzner Cloud:

- Server (cx22 = 2 vCPU / 4GB / 40GB — ~4€/month)
- Firewall (SSH, HTTP, HTTPS, Node Exporter)
- SSH key
- cloud-init (deploy user, ufw, fail2ban)
- Optional: floating IP, extra data volume

### Server types (Hetzner)

| Type | vCPU | RAM | Disk | ~Price |
|------|------|-----|------|--------|
| cx22 | 2 | 4 GB | 40 GB | 4€/mo |
| cx32 | 4 | 8 GB | 80 GB | 8€/mo |
| cx42 | 8 | 16 GB | 160 GB | 16€/mo |
| cx52 | 16 | 32 GB | 320 GB | 32€/mo |

---

## Project structure

```
infra-as-code/
├── ansible/
│   ├── ansible.cfg
│   ├── inventory/
│   │   ├── production/
│   │   │   ├── hosts.yml
│   │   │   └── group_vars/all.yml
│   │   └── staging/
│   │       └── hosts.yml
│   ├── roles/
│   │   ├── common/          # packages, user, SSH, sysctl, swap
│   │   ├── firewall/        # UFW
│   │   ├── fail2ban/        # fail2ban + nginx jails
│   │   ├── docker/          # Docker CE + Compose
│   │   ├── nginx/           # nginx + vhost templates
│   │   ├── ssl/             # Certbot + Let's Encrypt
│   │   └── monitoring/      # Node Exporter
│   └── playbooks/
│       ├── bootstrap.yml    # first run as root
│       ├── site.yml         # full setup
│       └── deploy.yml       # deploy app via compose-stacks
├── terraform/
│   ├── modules/
│   │   └── vps/             # Hetzner VPS + firewall + SSH key
│   └── environments/
│       └── production/      # main.tf, variables.tf, outputs.tf
├── .github/workflows/
│   └── ci.yml               # Ansible lint + Terraform fmt/validate
└── README.md
```

---

## CI

On every push: Ansible YAML lint → playbook syntax check → Terraform fmt → Terraform validate.

No real API calls are made in CI — Terraform uses dummy credentials for syntax validation only.

---

## Requirements

- Ansible 2.16+ with `community.general` and `ansible.posix` collections
- Terraform 1.10+
- Hetzner Cloud account and API token

```bash
# Install Ansible collections
ansible-galaxy collection install community.general ansible.posix

# Install Terraform
brew install terraform   # macOS
# or download from https://developer.hashicorp.com/terraform/downloads
```

---

## Changelog

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

---

## License

MIT
