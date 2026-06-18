terraform {
  required_version = ">= 1.10.0"

  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.48"
    }
  }

  # Uncomment to use Terraform Cloud for remote state:
  # cloud {
  #   organization = "your-org"
  #   workspaces { name = "infra-production" }
  # }
}

provider "hcloud" {
  token = var.hcloud_token
}

# ── Web server ────────────────────────────────────────────────────────────────
module "web01" {
  source = "../../modules/vps"

  name               = "web01"
  environment        = "production"
  server_type        = var.server_type
  location           = var.location
  ssh_public_key     = var.ssh_public_key
  ssh_port           = var.ssh_port
  ssh_allowed_ips    = var.ssh_allowed_ips
  monitoring_ips     = var.monitoring_ips
  timezone           = var.timezone
  enable_floating_ip = var.enable_floating_ip

  labels = {
    role    = "webserver"
    project = var.project_name
  }
}
