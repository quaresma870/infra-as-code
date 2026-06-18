output "staging_ip" {
  value = module.staging01.ipv4_address
}

output "staging_ssh" {
  value = module.staging01.ssh_command
}

output "ansible_inventory" {
  value = module.staging01.ansible_inventory_entry
}
