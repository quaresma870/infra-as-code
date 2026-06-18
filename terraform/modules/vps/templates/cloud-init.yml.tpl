#cloud-config
# Managed by Terraform

hostname: ${hostname}
manage_etc_hosts: true
timezone: ${timezone}

users:
  - name: ${deploy_user}
    groups: [sudo, docker]
    shell: /bin/bash
    sudo: ALL=(ALL) NOPASSWD:ALL
    ssh_authorized_keys:
      - ${ssh_key}

package_update: true
package_upgrade: true

packages:
  - curl
  - wget
  - git
  - vim
  - htop
  - ufw
  - fail2ban
  - ca-certificates
  - gnupg
  - python3
  - python3-apt

runcmd:
  - ufw allow 22/tcp
  - ufw allow 80/tcp
  - ufw allow 443/tcp
  - ufw --force enable
  - systemctl enable fail2ban
  - systemctl start fail2ban

final_message: |
  Cloud-init complete for ${hostname}.
  Deploy user: ${deploy_user}
  Run: ansible-playbook playbooks/site.yml -i inventory/production --limit ${hostname}
