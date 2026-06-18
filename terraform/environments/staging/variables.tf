variable "hcloud_token" {
  description = "Hetzner Cloud API token"
  type        = string
  sensitive   = true
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "myproject"
}

variable "server_type" {
  description = "Smaller type for staging (cx11 = 1 vCPU / 2GB)"
  type        = string
  default     = "cx11"
}

variable "location" {
  type    = string
  default = "nbg1"
}

variable "ssh_public_key" {
  type = string
}

variable "ssh_port" {
  type    = number
  default = 22
}

variable "ssh_allowed_ips" {
  type    = list(string)
  default = ["0.0.0.0/0", "::/0"]
}

variable "timezone" {
  type    = string
  default = "Europe/Lisbon"
}
