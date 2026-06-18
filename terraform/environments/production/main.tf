terraform {
  required_version = ">= 1.10.0"

  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.48"
    }
  }

  # ── Remote state backend (REQUIRED for team use) ──────────────────────────
  # Option A: Terraform Cloud (recommended)
  # cloud {
  #   organization = "your-org"
  #   workspaces { name = "infra-production" }
  # }

  # Option B: S3-compatible (Hetzner Object Storage, AWS S3, etc.)
  # backend "s3" {
  #   bucket         = "your-tfstate-bucket"
  #   key            = "production/terraform.tfstate"
  #   region         = "eu-west-1"
  #   encrypt        = true
  #   # For state locking (AWS only):
  #   dynamodb_table = "terraform-locks"
  #   # For Hetzner Object Storage:
  #   # endpoint = "https://fsn1.your-objectstorage.com"
  #   # skip_credentials_validation = true
  #   # skip_metadata_api_check     = true
  #   # skip_region_validation      = true
  #   # force_path_style            = true
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
