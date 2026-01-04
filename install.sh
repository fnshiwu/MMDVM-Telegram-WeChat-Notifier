#!/bin/bash
# =============================================================
# MMDVM Notifier 自动化安装与集成脚本 (2026 优化版)
# =============================================================

# 1. 强制切换读写模式
rpi-rw

echo "------------------------------------------------"
echo "🛠️  开始 MMDVM 推送工具全自动化安装..."
echo "------------------------------------------------"

# 2. 环境依赖检查
echo ">> [1/5] 检查系统环境..."
sudo apt-get update && sudo apt-get install -y python3-requests python3-pip
# 修复部分系统没有 pip 的问题
sudo pip3 install requests --upgrade 2>/dev/null

# 3. 核心文件部署
echo ">> [2/5] 部署后端与管理页面..."
# 确保在当前目录下操作
CUR_DIR=$(pwd)
sudo cp "$CUR_DIR/push_script.py" /home/pi-star/
sudo chmod +x /home/pi-star/push_script.py

sudo cp "$CUR_DIR/push_admin.php" /var/www/dashboard/admin/
sudo chown www-data:www-data /var/www/dashboard/admin/push_admin.php
sudo chmod 644 /var/www/dashboard/admin/push_admin.php

# 4. 菜单精准挂载 (核心优化)
echo ">> [3/5] 挂载管理菜单..."
ADMIN_INDEX="/var/www/dashboard/admin/index.php"

# 先清理可能存在的旧链接，防止重复挂载
sudo sed -i '/push_admin.php/d' "$ADMIN_INDEX"

# 使用正则表达式定位菜单栏结束标志，并在其前插入
# 逻辑：找到包含 'Dashboard' 的行，在其后面插入我们的菜单
if grep -q "Dashboard" "$ADMIN_INDEX"; then
    sudo sed -i "/'Dashboard'/a \  echo \" <a href=\\\"/admin/push_admin.php\\\" style=\\\"color: #ffffff;\\\">推送设置</a> | \";" "$ADMIN_INDEX"
    echo "✅ 菜单链接已挂载至 Dashboard 后侧"
else
    # 备选方案：如果找不到 Dashboard，则插在 Configuration 之前
    sudo sed -i "/'Configuration'/i \  echo \" <a href=\\\"/admin/push_admin.php\\\" style=\\\"color: #ffffff;\\\">推送设置</a> | \";" "$ADMIN_INDEX"
    echo "✅ 菜单链接已挂载至 Configuration 前侧"
fi

# 5. 权限与服务初始化
echo ">> [4/5] 初始化配置文件与服务..."
if [ ! -f "/etc/mmdvm_push.json" ]; then
    echo '{"push_tg_enabled":false,"push_wx_enabled":false,"my_callsign":"","tg_token":"","tg_chat_id":"","wx_token":"","ignore_list":[],"focus_list":[],"quiet_mode":{"enabled":false,"start_time":"23:00","end_time":"07:00"}}' | sudo tee /etc/mmdvm_push.json
fi
sudo chmod 666 /etc/mmdvm_push.json

# 部署 Systemd 服务
if [ -f "$CUR_DIR/mmdvm-push.service" ]; then
    sudo cp "$CUR_DIR/mmdvm-push.service" /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable mmdvm-push.service
    sudo systemctl restart mmdvm-push.service
    echo "✅ 服务已启动并设置开机自启"
fi

# 6. 完成提示
echo "------------------------------------------------"
echo "✨ 安装已成功完成！"
echo "1. 请在浏览器访问你的 Pi-Star 管理界面。"
echo "2. 你应该能在顶部菜单看到 [推送设置]。"
echo "3. 如果没看到，请尝试直接访问: http://$(hostname -I | awk '{print $1}')/admin/push_admin.php"
echo "------------------------------------------------"
