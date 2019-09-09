#!/bin/bash

# Name of new administrative user
USERNAME="admin"
# E-mail address where reports are sent to
EMAIL_NOTIFY="admin@example.com"
# SSH port
SSH_PORT="22"
# ossim-logarchiver port
WEB_PORT="4343"

set -euo pipefail

# Remove GDB, rpcbind, telnet, ftp
echo "Removing unused services and updating system..."
apt-get -qq remove -y gdb rpcbind telnet ftp
apt-get -qq autoremove -y
apt-get -qq update
apt-get -qq upgrade -y

# Disable C-M-DEL
echo "Disabling Ctrl+Alt+Del"
ln -sf /dev/null /lib/systemd/system/ctrl-alt-del.target

# Disable Magic SysRq
# echo "Disabling SysRq"
# sysctl -w kernel.sysrq=0

# Install tiger

echo "Installing tiger, please press 'Yes' to all prompts."
apt-get -qq install -y tiger


sed -re "s/Tiger_Mail_RCPT=\"root\"/Tiger_Mail_RCPT=\"$EMAIL_NOTIFY\"/g" -i /etc/tiger/tigerrc

# Create a new administrative user
echo "Creating a new user $USERNAME..."
useradd -m -d "/home/$USERNAME" -U -s /bin/bash $USERNAME
touch "/home/$USERNAME/.bash_history"
chattr +a "/home/$USERNAME/.bash_history"

echo "Please set a password for $USERNAME:"
passwd $USERNAME


# Install and configure sudo
echo "Installing sudo..."
apt-get -qq install -y sudo
gpasswd -a $USERNAME sudo


# Set default umask
echo "Setting default umask..."
sed -re "s/^UMASK.*/UMASK	077/" -i /etc/login.defs
echo "session optional pam_umask.so" >> /etc/pam.d/common-session

# SSH settings
echo "Generate an SSH public key using 'ssh-keygen' and do 'ssh-copy-id [adminuser@server_ip]'. Password logins will be disabled. Press any key to continue."
echo "[!] YOU WILL NOT BE ABLE TO LOG IN WITH YOUR PASSWORD OR THE ROOT ACCOUNT ANYMORE"
read -n1 asdf
echo "Securing SSH access..."

sed -r -e "s/PermitRootLogin yes/PermitRootLogin no/" \
       -e "s/\#PasswordAuthentication yes/PasswordAuthentication no/" \
       -e "s/Port 22/Port $SSH_PORT/" -i /etc/ssh/sshd_config

/etc/init.d/ssh restart

echo "SSH is now serving on *port $SSH_PORT*"
# Install fail2ban
echo "Installing fail2ban..."
apt-get -qq install -y fail2ban

# Set iptables rules
echo "Setting iptables rules"
sed -re "s/!SSH!/$SSH_PORT/g" -i ./firewall_rules
sed -re "s/!WEB!/$WEB_PORT/g" -i ./firewall_rules
echo -e '#!/bin/sh\n/sbin/iptables-restore < /etc/firewall_rules' > /etc/network/if-pre-up.d/iptables
source ./firewall_rules
/sbin/iptables-save > /etc/firewall_rules

echo "Setting ip6tables rules"
sed -re "s/!SSH!/$SSH_PORT/g" -i ./firewall_rules6
sed -re "s/!WEB!/$WEB_PORT/g" -i ./firewall_rules6
echo -e '#!/bin/sh\n/sbin/ip6tables-restore < /etc/firewall_rules6' > /etc/network/if-pre-up.d/ip6tables
source ./firewall_rules6
/sbin/ip6tables-save > /etc/firewall_rules6

# Add session logging
echo "Enabling session logging"
mkdir -p /var/log/sessions
chmod 1777 /var/log/sessions
chattr +a /var/log/sessions
echo 'exec script -q -a "/var/log/sessions/$USER-`date +%Y-%m-%d`"' >> /etc/profile

# Enable auditing
echo "Enabling auditing"
apt-get -qq -y install auditd

# nginx security - see server install script

# separate user for server application - see server install script
