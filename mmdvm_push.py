import os
import time
import json
import glob
import re
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

# ================= [路径配置] =================
CONFIG_FILE = "/etc/mmdvm_push.json"
LOG_DIR = "/var/log/pi-star/"
MIN_DURATION = 0.5  # 捕捉超过 0.5 秒的通联
# =============================================

def load_config():
    """动态读取由 PHP 页面生成的 JSON 配置文件"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"❌ 配置文件读取异常: {e}")
    return None

def send_tg(text, config):
    """使用 Python 内置库发送 Telegram 消息"""
    if not config or not config.get('push_tg_enabled'): return
    token = config.get('tg_token')
    chat_id = config.get('tg_chat_id')
    
    params = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    })
    url = f"https://api.telegram.org/bot{token}/sendMessage?{params}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return response.read()
    except Exception as e:
        print(f"❌ TG 发送失败: {e}")

def send_wx(title, content, config):
    """使用 Python 内置库发送微信 (PushPlus) 消息"""
    if not config or not config.get('push_wx_enabled'): return
    token = config.get('wx_token')
    url = 'http://www.pushplus.plus/send'
    
    data = {
        "token": token,
        "title": title,
        "content": content,
        "template": "html"
    }
    json_data = json.dumps(data).encode('utf-8')
    
    try:
        req = urllib.request.Request(url, data=json_data, method='POST')
        req.add_header('Content-Type', 'application/json; charset=utf-8')
        with urllib.request.urlopen(req, timeout=10) as response:
            res_text = response.read().decode('utf-8')
            print(f"📡 微信推送反馈: {res_text}")
    except Exception as e:
        print(f"❌ 微信推送连接失败: {e}")

def get_latest_log():
    """获取 /var/log/pi-star/ 目录下最近修改的 MMDVM 日志文件"""
    log_files = glob.glob(os.path.join(LOG_DIR, "MMDVM-*.log"))
    if not log_files: return None
    return max(log_files, key=os.path.getmtime)

def monitor_log():
    current_log_path = get_latest_log()
    if not current_log_path:
        print("❌ 错误：未找到 MMDVM 日志文件，请检查 Pi-Star 是否正常运行")
        return
    
    print(f"🚀 监控已启动，当前追踪: {current_log_path}")
    
    while True:
        try:
            # 每次循环开始前，确保配置是最新的
            config = load_config()
            if not config:
                time.sleep(5)
                continue

            with open(current_log_path, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(0, 2) # 跳到文件末尾开始实时监听
                while True:
                    # 自动检测日志轮转（处理凌晨跨天文件名切换）
                    new_log_path = get_latest_log()
                    if new_log_path and new_log_path != current_log_path:
                        current_log_path = new_log_path
                        print(f"📅 日志已更名或跨天，切换至: {current_log_path}")
                        break 

                    line = f.readline()
                    if not line:
                        time.sleep(0.4) # 稍作休眠减少系统开销
                        continue
                    
                    # 核心匹配逻辑：识别通联结束标志
                    if "end of" in line and "transmission" in line:
                        # 排除掉自己的通联记录
                        my_call = config.get('my_callsign', 'NONE').upper()
                        if my_call in line.upper():
                            continue

                        # 1. 区分通联类型：话音 或 数据
                        is_voice = "voice" in line.lower()
                        mode_icon = "🎙️ 话音通联结束" if is_voice else "💾 数据传输结束"

                        # 2. 提取时长 (Seconds)
                        duration_match = re.search(r'(\d+\.?\d*)\s+seconds', line)
                        duration_val = float(duration_match.group(1)) if duration_match else 0.0
                        
                        # 3. 提取来源呼号 (From)
                        call_match = re.search(r'from\s+([A-Z0-9/]+)', line)
                        remote_call = call_match.group(1) if call_match else "未知呼号"
                        
                        # 黑名单过滤
                        if remote_call in config.get('ignore_list', []):
                            print(f"🚫 已拦截黑名单呼号: {remote_call}")
                            continue

                        # 4. 提取目标群组 (To)
                        tg_match = re.search(r'to\s+(TG\s*\d+|PC\s*\d+|Reflector\s*\d+|\d+)', line)
                        target_tg = tg_match.group(1) if tg_match else "未知群组"

                        # 5. 处理时间 (将日志的 UTC 转为北京时间)
                        time_match = re.search(r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}', line)
                        if time_match:
                            utc_time = datetime.strptime(time_match.group(), "%Y-%m-%d %H:%M:%S")
                            bj_now = utc_time + timedelta(hours=8)
                        else:
                            bj_now = datetime.now()

                        date_str = bj_now.strftime("%Y-%m-%d")
                        time_str = bj_now.strftime("%H:%M:%S")

                        # 6. 识别时隙 (Slot)
                        slot = "1" if "Slot 1" in line else "2"

                        # --- 构建精美推送格式 ---
                        # TG 专用（Markdown）
                        msg_tg = (
                            f"*{mode_icon}*\n"
                            f"--- \n"
                            f"👤 呼号: {remote_call}\n"
                            f"👥 群组: {target_tg}\n"
                            f"📅 日期: {date_str}\n"
                            f"⏰ 时间: {time_str}\n"
                            f"📡 时隙: {slot}\n"
                            f"⏳ 时长: {duration_val}s"
                        )

                        # 微信专用（HTML）
                        msg_wx = (
                            f"<b>{mode_icon}</b><br>"
                            f"--- <br>"
                            f"👤 呼号: {remote_call}<br>"
                            f"👥 群组: {target_tg}<br>"
                            f"📅 日期: {date_str}<br>"
                            f"⏰ 时间: {time_str}<br>"
                            f"📡 时隙: {slot}<br>"
                            f"⏳ 时长: {duration_val}s"
                        )

                        # 执行推送动作
                        send_tg(msg_tg, config)
                        send_wx(mode_icon, msg_wx, config)
                        print(f"✅ 推送成功: {remote_call} | {date_str} {time_str} | {duration_val}s")

        except Exception as e:
            print(f"⚠️ 系统异常: {e}")
            time.sleep(5) # 异常后等待 5 秒重新进入循环

if __name__ == "__main__":
    monitor_log()
