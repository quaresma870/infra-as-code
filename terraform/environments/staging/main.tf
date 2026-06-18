terraform {
  required_version = ">= 1.10.0"

  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.48"
    }
  }
}

provider "hcloud" {
  token = var.hcloud_token
}

# ── Staging web server (smaller than production) ──────────────────────────────
module "staging01" {
  source = "../../modules/vps"

  name               = "staging01"
  environment        = "staging"
  server_type        = var.server_type
  location           = var.location
  ssh_public_key     = var.ssh_public_key
  ssh_port           = var.ssh_port
  ssh_allowed_ips    = var.ssh_allowed_ips
  timezone           = var.timezone
  enable_floating_ip = false

  labels = {
    role    = "webserver"
    project = var.project_name
  }
}
