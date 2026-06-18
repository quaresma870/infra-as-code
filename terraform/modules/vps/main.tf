# ── VPS module ────────────────────────────────────────────────────────────────
# Generic VPS module — implemented for Hetzner Cloud.
# Swap the provider block to adapt to DigitalOcean, Linode, OVH, etc.

terraform {
  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.48"
    }
  }
}

# ── SSH Key ───────────────────────────────────────────────────────────────────
resource "hcloud_ssh_key" "deploy" {
  name       = "${var.name}-deploy-key"
  public_key = var.ssh_public_key
}

# ── Firewall ──────────────────────────────────────────────────────────────────
resource "hcloud_firewall" "server" {
  name = "${var.name}-firewall"

  # SSH
  rule {
    direction  = "in"
    protocol   = "tcp"
    port       = tostring(var.ssh_port)
    source_ips = var.ssh_allowed_ips
    description = "SSH access"
  }

  # HTTP
  rule {
    direction   = "in"
    protocol    = "tcp"
    port        = "80"
    source_ips  = ["0.0.0.0/0", "::/0"]
    description = "HTTP"
  }

  # HTTPS
  rule {
    direction   = "in"
    protocol    = "tcp"
    port        = "443"
    source_ips  = ["0.0.0.0/0", "::/0"]
    description = "HTTPS"
  }

  # Node Exporter (monitoring subnet only)
  dynamic "rule" {
    for_each = var.monitoring_ips
    content {
      direction   = "in"
      protocol    = "tcp"
      port        = "9100"
      source_ips  = [rule.value]
      description = "Node Exporter from monitoring"
    }
  }

  # ICMP (ping)
  rule {
    direction  = "in"
    protocol   = "icmp"
    source_ips = ["0.0.0.0/0", "::/0"]
  }
}

# ── Server ────────────────────────────────────────────────────────────────────
resource "hcloud_server" "main" {
  name        = var.name
  server_type = var.server_type
  image       = var.image
  location    = var.location
  ssh_keys    = [hcloud_ssh_key.deploy.id]

  firewall_ids = [hcloud_firewall.server.id]

  labels = merge(var.labels, {
    managed_by  = "terraform"
    environment = var.environment
  })

  # User data — cloud-init for initial setup
  user_data = templatefile("${path.module}/templates/cloud-init.yml.tpl", {
    hostname    = var.name
    deploy_user = var.deploy_user
    ssh_key     = var.ssh_public_key
    timezone    = var.timezone
  })

  lifecycle {
    ignore_changes = [user_data, ssh_keys]
  }
}

# ── Floating IP (optional) ────────────────────────────────────────────────────
resource "hcloud_floating_ip" "main" {
  count         = var.enable_floating_ip ? 1 : 0
  type          = "ipv4"
  home_location = var.location
  name          = "${var.name}-floating-ip"
  labels        = { managed_by = "terraform" }
}

resource "hcloud_floating_ip_assignment" "main" {
  count          = var.enable_floating_ip ? 1 : 0
  floating_ip_id = hcloud_floating_ip.main[0].id
  server_id      = hcloud_server.main.id
}

# ── Volume (optional extra disk) ──────────────────────────────────────────────
resource "hcloud_volume" "data" {
  count    = var.extra_volume_gb > 0 ? 1 : 0
  name     = "${var.name}-data"
  size     = var.extra_volume_gb
  location = var.location
  format   = "ext4"
  labels   = { managed_by = "terraform" }
}

resource "hcloud_volume_attachment" "data" {
  count     = var.extra_volume_gb > 0 ? 1 : 0
  volume_id = hcloud_volume.data[0].id
  server_id = hcloud_server.main.id
  automount = true
}
