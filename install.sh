#!/bin/bash
# MMDVM Push Tool for Pi-Star - Auto Installer
rpi-rw

# 1. 创建配置文件 / Create Config File
if [ ! -f /etc/mmdvm_push.json ]; then
cat <<EOF | sudo tee /etc/mmdvm_push.json
{
  "push_tg_enabled": false,
  "push_wx_enabled": false,
  "my_callsign": "BA4SMQ",
  "tg_token": "",
  "tg_chat_id": "",
  "wx_token": "",
  "ignore_list": [],
  "focus_list": [],
  "min_duration": 5.0,
  "quiet_mode": {"enabled": false, "start_time": "23:00", "end_time": "07:00"}
}
EOF
fi

# 2. 设置权限 / Set Permissions
sudo chown www-data:www-data /etc/mmdvm_push.json
sudo chmod 666 /etc/mmdvm_push.json

# 3. 集成 Web 菜单 / Integrate Web Menu
ADMIN_INDEX="/var/www/dashboard/admin/index.php"
if ! grep -q "push_admin.php" "$ADMIN_INDEX"; then
    sudo sed -i '/configure.php/i \  echo " <a href=\"/admin/push_admin.php\" style=\"color: #ffffff;\">推送设置</a> |";' "$ADMIN_INDEX"
fi

echo "Install complete. Please upload push_admin.php to /var/www/dashboard/admin/"
