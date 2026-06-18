variable "name" {
  description = "Server name"
  type        = string
}

variable "environment" {
  description = "Environment: production, staging, dev"
  type        = string
  default     = "production"
}

variable "server_type" {
  description = "Hetzner server type (e.g. cx22, cx32, cx42)"
  type        = string
  default     = "cx22"   # 2 vCPU, 4GB RAM — ~4€/month
}

variable "image" {
  description = "OS image"
  type        = string
  default     = "ubuntu-24.04"
}

variable "location" {
  description = "Datacenter location (nbg1=Nuremberg, fsn1=Falkenstein, hel1=Helsinki)"
  type        = string
  default     = "nbg1"
}

variable "ssh_public_key" {
  description = "SSH public key content"
  type        = string
}

variable "ssh_port" {
  description = "SSH port"
  type        = number
  default     = 22
}

variable "ssh_allowed_ips" {
  description = "IPs allowed to SSH. Use ['0.0.0.0/0'] to allow all (not recommended)"
  type        = list(string)
  default     = ["0.0.0.0/0", "::/0"]
}

variable "monitoring_ips" {
  description = "IPs allowed to scrape Node Exporter (port 9100)"
  type        = list(string)
  default     = []
}

variable "deploy_user" {
  description = "Non-root deploy user created via cloud-init"
  type        = string
  default     = "deploy"
}

variable "timezone" {
  description = "Server timezone"
  type        = string
  default     = "Europe/Lisbon"
}

variable "enable_floating_ip" {
  description = "Assign a floating IP to the server"
  type        = bool
  default     = false
}

variable "extra_volume_gb" {
  description = "Size of extra data volume in GB. 0 = no volume"
  type        = number
  default     = 0
}

variable "labels" {
  description = "Additional labels for Hetzner resources"
  type        = map(string)
  default     = {}
}
