#!/bin/bash
# =============================================================
# MMDVM Telegram/WeChat Notifier 终极安装脚本
# 适配权限锁定的 Pi-Star 系统 & 2026 最新日志格式
# =============================================================

# 1. 环境准备
rpi-rw
CUR_DIR=$(pwd)
ADMIN_DIR="/var/www/dashboard/admin"
ADMIN_INDEX="$ADMIN_DIR/index.php"

echo "------------------------------------------------"
echo "⚙️  正在开始精准安装..."

# 2. 解锁目录权限 (解决 ls -ld 显示的 dr-xr-xr-x 问题)
echo ">> [1/5] 解锁系统目录权限..."
sudo chmod +w "$ADMIN_DIR"

# 3. 部署管理页面
echo ">> [2/5] 部署管理页面..."
if [ -f "$CUR_DIR/push_admin.php" ]; then
    sudo cp "$CUR_DIR/push_admin.php" "$ADMIN_DIR/"
    sudo chown www-data:www-data "$ADMIN_DIR/push_admin.php"
    sudo chmod 644 "$ADMIN_DIR/push_admin.php"
fi

# 4. 注入菜单链接 (适配你的 grep 结果)
echo ">> [3/5] 注入管理菜单..."
# 清理旧痕迹
sudo sed -i '/push_admin.php/d' "$ADMIN_INDEX"
# 精准注入：匹配 update.php 那行 PHP echo
if grep -q "update.php" "$ADMIN_INDEX"; then
    sudo sed -i '/update.php/a \  echo \" <a href=\\\"/admin/push_admin.php\\\" style=\\\"color: #ffffff;\\\">推送设置</a> | \";' "$ADMIN_INDEX"
    echo "✅ 菜单链接注入成功"
fi

# 还原目录权限
sudo chmod -w "$ADMIN_DIR"

# 5. 初始化配置与后台脚本
echo ">> [4/5] 部署推送引擎..."
# 确保配置文件夹存在并可写
if [ ! -f "/etc/mmdvm_push.json" ]; then
    echo '{"push_tg_enabled":false,"push_wx_enabled":false,"my_callsign":"","tg_token":"","tg_chat_id":"","wx_token":"","ignore_list":[],"focus_list":[],"quiet_mode":{"enabled":false,"start_time":"23:00","end_time":"07:00"}}' | sudo tee /etc/mmdvm_push.json
fi
sudo chmod 666 /etc/mmdvm_push.json

# 部署 Python 脚本
sudo cp "$CUR_DIR/push_script.py" /home/pi-star/
sudo chmod +x /home/pi-star/push_script.py

# 6. 配置 Systemd 服务
echo ">> [5/5] 配置开机自启服务..."
if [ -f "$CUR_DIR/mmdvm-push.service" ]; then
    sudo cp "$CUR_DIR/mmdvm-push.service" /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable mmdvm-push.service
    sudo systemctl restart mmdvm-push.service
    echo "✅ 服务已启动"
fi

echo "------------------------------------------------"
echo "✨ 安装成功！"
echo "请在 Pi-Star 页面点击 [推送设置] 进行配置。"
echo "------------------------------------------------"
