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
│   │   ├── firewall/        # UFW — has Molecule tests (roles/firewall/molecule/)
│   │   ├── fail2ban/        # fail2ban + nginx jails
│   │   ├── docker/          # Docker CE + Compose — has Molecule tests
│   │   ├── haproxy/         # HAProxy load balancer
│   │   ├── nginx/           # nginx + vhost templates
│   │   ├── ssl/             # Certbot + Let's Encrypt — has Molecule tests
│   │   ├── monitoring/      # Node Exporter
│   │   └── backup/          # automated cron backups
│   └── playbooks/
│       ├── bootstrap.yml    # first run as root
│       ├── site.yml         # full setup
│       └── deploy.yml       # deploy app via compose-stacks
├── terraform/
│   ├── modules/
│   │   └── vps/             # Hetzner VPS + firewall + SSH key
│   └── environments/
│       ├── production/      # main.tf, variables.tf, outputs.tf
│       └── staging/
├── .github/workflows/
│   └── ci.yml               # lint + Molecule + Terraform fmt/validate
└── README.md
```

---

## CI

On every push: YAML lint → playbook syntax check → ansible-lint (`production`
profile) → **Molecule tests** (firewall/docker/ssl roles, real Docker
containers, real assertions — not just "did it run without erroring") →
Terraform fmt → Terraform validate.

No real API calls are made in CI — Terraform uses dummy credentials for
syntax validation only. Molecule tests run for real, against real (containerized)
hosts.

**Optional repo secrets** — `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN`: if set,
the Molecule job logs in to Docker Hub before pulling test images, raising
the pull rate limit well above the anonymous tier. Not required — without
them, Molecule still runs exactly the same way, just with a (real, observed
while building this) risk of occasionally hitting Docker Hub's anonymous
rate limit on a busy day. A free Docker Hub account + a read-only access
token is enough; no paid plan needed.

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

See [CHANGELOG.md](CHANGELOG.md) for release history.

---

## License

MIT
