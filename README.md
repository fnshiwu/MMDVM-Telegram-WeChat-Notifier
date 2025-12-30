# MMDVM-Telegram-Beacon-
基于树莓派 MMDVM 盒子的 Telegram 通联实时监控机器人。
本教程专为使用 Pi-Star 系统的 树莓派 Zero W + 双工板 用户设计，支持北京时间转换、Markdown 精美排版、呼号过滤及跨天日志自动切换。

🌟 功能特性
实时推送：有人通联时，手机 Telegram 秒收消息。

北京时间：自动将 MMDVM 日志的 UTC 时间转换为 UTC+8。

精美排版：使用 Markdown 语法，关键信息（时间、呼号）一目了然。

自动过滤：支持设置白名单，自动过滤自己的呼号，避免“自己吵到自己”。

无感运行：支持开机自启，自动检测跨天日志切换，无需每日重启。

🛠️ 准备工作
硬件：运行 Pi-Star 系统的 MMDVM 盒子。

机器人：

在 Telegram 关注 @BotFather，创建机器人并获取 API Token。

向你的机器人发送 /start。

访问 https://api.telegram.org/bot<你的Token>/getUpdates 获取你的 Chat ID。

🚀 安装步骤
1. 登录树莓派并开启读写模式
通过 SSH 登录你的 Pi-Star，执行：

Bash

rpi-rw
2. 创建监控脚本
创建并编辑 Python 脚本：

Bash

nano ~/mmdvm_notify.py
粘贴以下完整代码（请务必修改配置区域）：

Python

import time
import requests
import os
import glob
from datetime import datetime, timedelta

# ================= [配置区域] =================
TOKEN = "你的_Telegram_Bot_Token"
CHAT_ID = "你的_Chat_ID"
MY_CALLSIGN = "你的呼号"  # 例如: BA4SMQ
LOG_DIR = "/var/log/pi-star/"
# =============================================

def send_msg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.get(url, params=params, timeout=10)
    except:
        pass

def get_latest_log():
    log_files = glob.glob(os.path.join(LOG_DIR, "MMDVM-*.log"))
    return max(log_files, key=os.path.getmtime) if log_files else None

def monitor_log():
    current_log_path = get_latest_log()
    if not current_log_path: return
    
    while True:
        with open(current_log_path, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(0, 2)
            while True:
                new_log_path = get_latest_log()
                if new_log_path != current_log_path:
                    current_log_path = new_log_path
                    break 

                line = f.readline()
                if not line:
                    time.sleep(0.5)
                    continue
                
                if "received network voice header" in line or "RF voice header" in line:
                    if MY_CALLSIGN.upper() in line.upper():
                        continue

                    try:
                        log_time_str = line[3:22]
                        utc_time = datetime.strptime(log_time_str, "%Y-%m-%d %H:%M:%S")
                        bj_time = utc_time + timedelta(hours=8)
                        bj_time_str = bj_time.strftime("%H:%M:%S")
                    except:
                        bj_time_str = datetime.now().strftime("%H:%M:%S")

                    content = line[line.find("DMR"):] if "DMR" in line else line.strip()
                    msg = (f"🔔 *MMDVM 实时通话*\n---\n"
                           f"⏰ *时间*: `{bj_time_str}`\n"
                           f"🎙️ *状态*: `监听到信号` \n"
                           f"📜 *详情*: \n`{content.strip()}`")
                    send_msg(msg)

if __name__ == "__main__":
    monitor_log()
3. 设置开机自启动
为了让脚本在后台稳定运行并开机自启，我们需要创建一个系统服务：

Bash

sudo nano /etc/systemd/system/mmdvm_notify.service
填入以下内容：

Ini, TOML

[Unit]
Description=MMDVM Telegram Bot
After=network.target mmdvmhost.service

[Service]
User=root
ExecStart=/usr/bin/python3 /home/pi-star/mmdvm_notify.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
4. 激活并运行
Bash

sudo systemctl daemon-reload
sudo systemctl enable mmdvm_notify.service
sudo systemctl start mmdvm_notify.service
📊 常用指令
查看运行状态：sudo systemctl status mmdvm_notify.service

重启机器人：sudo systemctl restart mmdvm_notify.service

停止推送：sudo systemctl stop mmdvm_notify.service

查看实时调试日志：journalctl -u mmdvm_notify.service -f

⚠️ 注意事项
网络环境：请确保你的树莓派能够正常连接 Telegram 服务器。

只读模式：Pi-Star 重启后会恢复只读模式，如需修改脚本，请先执行 rpi-rw。

零点切换：本脚本已包含自动检测逻辑，无需担心跨天不推送的问题。

73! Hope to meet you on the air.

如果您觉得这个教程有帮助，欢迎在 GitHub 上点一个 Star！
