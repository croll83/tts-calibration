terraform {
  required_providers {
    proxmox = {
      source  = "Telmate/proxmox"
      version = "~> 2.9"
    }
  }
}

provider "proxmox" {
  pm_api_url          = var.proxmox_api_url
  pm_api_token_id     = var.proxmox_api_token_id
  pm_api_token_secret = var.proxmox_api_token_secret
  pm_tls_insecure     = true
}

variable "proxmox_api_url" {
  default = "https://192.168.1.49:8006/api2/json"
}

variable "proxmox_api_token_id" {
  description = "API token ID (es. root@pam!terraform)"
  default     = "root@pam!terraform"
}

variable "proxmox_api_token_secret" {
  description = "API token secret"
  sensitive   = true
}

variable "proxmox_node" {
  default = "proxmox"
}

variable "ssh_public_key" {
  default = ""
}

resource "proxmox_lxc" "tts_calibration" {
  hostname    = "tts-calibration"
  target_node = var.proxmox_node
  ostemplate  = "local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst"

  cores  = 2
  memory = 2048
  swap   = 512

  rootfs {
    storage = "local-lvm"
    size    = "10G"
  }

  network {
    name   = "eth0"
    bridge = "vmbr0"
    ip     = "dhcp"
  }

  features {
    nesting = true  # necessario per Docker
    keyctl  = true
  }

  start        = true
  unprivileged = true

  ssh_public_keys = var.ssh_public_key

  tags = "jarvis,calibration,temp"
}

output "lxc_id" {
  value = proxmox_lxc.tts_calibration.vmid
}
