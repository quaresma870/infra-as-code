variable "hcloud_token" {
  description = "Hetzner Cloud API token"
  type        = string
  sensitive   = true
}

variable "project_name" {
  description = "Project name for labelling resources"
  type        = string
  default     = "myproject"
}

variable "domain" {
  description = "Primary domain"
  type        = string
  default     = "example.com"
}

variable "server_type" {
  description = "Hetzner server type"
  type        = string
  default     = "cx22"
}

variable "location" {
  description = "Datacenter: nbg1, fsn1, hel1, ash (USA), hil (USA)"
  type        = string
  default     = "nbg1"
}

variable "ssh_public_key" {
  description = "SSH public key content for deploy user"
  type        = string
}

variable "ssh_port" {
  description = "SSH port"
  type        = number
  default     = 22
}

variable "ssh_allowed_ips" {
  description = "IPs allowed to SSH"
  type        = list(string)
  default     = ["0.0.0.0/0", "::/0"]
}

variable "monitoring_ips" {
  description = "IPs that may scrape Node Exporter (port 9100)"
  type        = list(string)
  default     = []
}

variable "timezone" {
  description = "Server timezone"
  type        = string
  default     = "Europe/Lisbon"
}

variable "enable_floating_ip" {
  description = "Assign a floating IP"
  type        = bool
  default     = false
}
