#!/bin/bash

echo "Creating user 'tunnel'..."
PASSWD=`hexdump -n 12 -v -e '/1 "%02x"' /dev/urandom`
useradd -s /bin/false -M tunnel
echo -e "$PASSWD\n$PASSWD" | passwd tunnel

if [ $? -eq 0 ]; then
    echo "Account successfully created, password is $PASSWD"
else
    echo "Account creation failed! Perhaps it's already been created?"
    exit 1
fi

cat <<EOF >> /etc/ssh/sshd_config
Match User tunnel
   X11Forwarding no
   PermitTunnel no
   GatewayPorts no
   AllowAgentForwarding no
   PermitOpen 127.0.0.1:3306
   ForceCommand echo 'This account is locked."
EOF

/etc/init.d/ssh restart
