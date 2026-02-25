terraform {
  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = "~> 0.97"
    }
  }
}

provider "proxmox" {
  endpoint  = var.proxmox_api_url
  api_token = var.proxmox_api_token
  insecure  = true
}

variable "proxmox_api_url" {
  default = "https://192.168.1.49:8006/"
}

variable "proxmox_api_token" {
  description = "API token (es. root@pam!terraform=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)"
  sensitive   = true
}

variable "proxmox_node" {
  default = "pve-wagmi"
}

variable "ssh_public_key" {
  default = ""
}

resource "proxmox_virtual_environment_container" "tts_calibration" {
  node_name    = var.proxmox_node
  unprivileged = true
  started      = true
  tags         = ["jarvis", "calibration", "temp"]

  operating_system {
    template_file_id = "local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst"
    type             = "debian"
  }

  cpu {
    cores = 2
  }

  memory {
    dedicated = 2048
    swap      = 512
  }

  disk {
    datastore_id = "local-lvm"
    size         = 10
  }

  features {
    nesting = true
  }

  initialization {
    hostname = "tts-calibration"

    ip_config {
      ipv4 {
        address = "dhcp"
      }
    }

    user_account {
      keys = var.ssh_public_key != "" ? [var.ssh_public_key] : []
    }
  }

  network_interface {
    name   = "eth0"
    bridge = "vmbr0"
  }
}

output "lxc_id" {
  value = proxmox_virtual_environment_container.tts_calibration.vm_id
}
