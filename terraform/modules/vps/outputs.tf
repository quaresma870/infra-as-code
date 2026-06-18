output "server_id" {
  description = "Hetzner server ID"
  value       = hcloud_server.main.id
}

output "ipv4_address" {
  description = "Server public IPv4 address"
  value       = hcloud_server.main.ipv4_address
}

output "ipv6_address" {
  description = "Server public IPv6 address"
  value       = hcloud_server.main.ipv6_address
}

output "floating_ip" {
  description = "Floating IP address (if enabled)"
  value       = var.enable_floating_ip ? hcloud_floating_ip.main[0].ip_address : null
}

output "volume_id" {
  description = "Extra data volume ID (if created)"
  value       = var.extra_volume_gb > 0 ? hcloud_volume.data[0].id : null
}

output "firewall_id" {
  description = "Hetzner firewall ID"
  value       = hcloud_firewall.server.id
}

output "ssh_command" {
  description = "SSH command to connect to the server"
  value       = "ssh -i ~/.ssh/deploy_key ${var.deploy_user}@${hcloud_server.main.ipv4_address}"
}

output "ansible_inventory_entry" {
  description = "Ansible inventory snippet for this server"
  value       = <<-EOT
    ${var.name}:
      ansible_host: ${hcloud_server.main.ipv4_address}
      ansible_port: ${var.ssh_port}
  EOT
}
