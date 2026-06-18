output "web01_ip" {
  description = "web01 public IPv4"
  value       = module.web01.ipv4_address
}

output "web01_ssh" {
  description = "SSH command for web01"
  value       = module.web01.ssh_command
}

output "ansible_inventory" {
  description = "Ansible inventory snippet — paste into inventory/production/hosts.yml"
  value       = module.web01.ansible_inventory_entry
}
