#!/bin/bash
# =============================================================
# MMDVM Telegram/WeChat Notifier 自动化安装脚本 (2026 兼容版)
# 设计者: BA4SMQ
# =============================================================

# 1. 开启读写模式
rpi-rw

echo "------------------------------------------------"
echo "🛠️  正在启动 MMDVM 推送工具安装程序..."
echo "------------------------------------------------"

# 2. 检查并安装必要依赖
echo ">> [1/5] 检查系统依赖环境..."
sudo apt-get update && sudo apt-get install -y python3-requests python3-pip
# 确保 requests 库可用
sudo pip3 install requests --upgrade 2>/dev/null

# 3. 部署核心文件
echo ">> [2/5] 正在部署脚本与管理页面..."
CUR_DIR=$(pwd)

# 部署后端监控脚本
if [ -f "$CUR_DIR/push_script.py" ]; then
    sudo cp "$CUR_DIR/push_script.py" /home/pi-star/
    sudo chmod +x /home/pi-star/push_script.py
    echo "✅ 后端脚本已就绪"
else
    echo "❌ 错误: 当前目录未找到 push_script.py"
    exit 1
fi

# 部署前端管理页面
if [ -f "$CUR_DIR/push_admin.php" ]; then
    sudo cp "$CUR_DIR/push_admin.php" /var/www/dashboard/admin/
    sudo chown www-data:www-data /var/www/dashboard/admin/push_admin.php
    sudo chmod 644 /var/www/dashboard/admin/push_admin.php
    echo "✅ 管理页面已就绪"
else
    echo "❌ 错误: 当前目录未找到 push_admin.php"
    exit 1
fi

# 4. 菜单挂载 (基于路径匹配的高兼容性方案)
echo ">> [3/5] 正在集成至 Pi-Star 菜单..."
ADMIN_INDEX="/var/www/dashboard/admin/index.php"

# 先清理可能存在的旧链接，防止重复挂载
sudo sed -i '/push_admin.php/d' "$ADMIN_INDEX"

# 核心逻辑：在包含 href="/admin/" 的行后面插入菜单链接
# 这样无论系统是中文还是英文，都能通过路径精准定位
if grep -q "href=\"/admin/\"" "$ADMIN_INDEX"; then
    sudo sed -i '/href="\/admin\/"/a <a href="/admin/push_admin.php" style="color: #ffffff;">推送设置</a> |' "$ADMIN_INDEX"
    echo "✅ 菜单链接挂载成功"
else
    # 备选方案：如果找不到特定路径，则尝试在 nav 标签后插入
    sudo sed -i '/id="nav"/a \  echo \" <a href=\\\"/admin/push_admin.php\\\" style=\\\"color: #ffffff;\\\">推送设置</a> | \";' "$ADMIN_INDEX"
    echo "✅ 采用备选方案挂载菜单"
fi

# 5. 权限与服务初始化
echo ">> [4/5] 正在配置守护进程与配置文件..."

# 初始化配置文件
if [ ! -f "/etc/mmdvm_push.json" ]; then
    echo '{"push_tg_enabled":false,"push_wx_enabled":false,"my_callsign":"","tg_token":"","tg_chat_id":"","wx_token":"","ignore_list":[],"focus_list":[],"quiet_mode":{"enabled":false,"start_time":"23:00","end_time":"07:00"}}' | sudo tee /etc/mmdvm_push.json
fi
sudo chmod 666 /etc/mmdvm_push.json

# 配置并启动 Systemd 服务
if [ -f "$CUR_DIR/mmdvm-push.service" ]; then
    sudo cp "$CUR_DIR/mmdvm-push.service" /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable mmdvm-push.service
    sudo systemctl restart mmdvm-push.service
    echo "✅ 后台推送服务已启动"
fi

# 6. 安装完成
echo "------------------------------------------------"
echo "✨ 安装完成！祝您通联愉快 73!"
echo "1. 刷新 Pi-Star 管理后台即可看到 [推送设置] 菜单。"
echo "2. 若菜单未出现，请尝试直接访问: http://$(hostname -I | awk '{print $1}')/admin/push_admin.php"
echo "------------------------------------------------"
