#!/bin/bash
set -e
echo "=== AKAKAKAKAKAKAKAKAKAKAKAK ==="
echo "=== VPN Panel Auto Installer ==="
echo "=== AKAKAKAKAKAKAKAKAKAKAKAK ==="


DOMAIN_NAME="(ip addr show $(ip route | awk '/default/ { print $5 }') | grep "inet " | awk '{print $2}' | cut -d'/' -f1)"
APP_DIR="/opt/vpnpanel"
REPO_URL="https://github.com/DEAD-EYE-AKPRO/vpnpanel.git"
FLASK_PORT="1227"
chmod +x openvpn-install.sh

echo "[*] Installing system dependencies..."
apt update
apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx sudo

echo "[*] Setting up application directory..."
mkdir -p $APP_DIR

echo "[*] Copying panel files..."
cp -r * $APP_DIR


echo "[*] Setting up Python environment..."
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt


echo "[*] Creating systemd service..."
cat <<EOF >/etc/systemd/system/vpnpanel.service
[Unit]
Description=VPN Panel
After=network.target

[Service]
User=root
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable vpnpanel
systemctl start vpnpanel

# Configure nginx
echo "[*] Configuring nginx reverse proxy..."
cat <<EOF >/etc/nginx/sites-available/vpnpanel
server {
    listen 80;
    server_name $DOMAIN_NAME;

    location / {
        proxy_pass http://127.0.0.1:$FLASK_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

ln -s /etc/nginx/sites-available/vpnpanel /etc/nginx/sites-enabled/vpnpanel
nginx -t && systemctl reload nginx

# Obtain certificate
echo "[*] Getting Let's Encrypt certificate..."
certbot --nginx -d $DOMAIN_NAME

echo "[*] Installation complete!"
echo "VPN Panel is now available at: https://$DOMAIN_NAME"
