import os, time, json, glob, re, urllib.request, urllib.parse
from datetime import datetime

CONFIG_FILE = "/etc/mmdvm_push.json"
LOG_DIR = "/var/log/pi-star/"

def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except: pass
    return {}

def is_quiet_time(config):
    qm = config.get('quiet_mode', {})
    if not qm.get('enabled', False): return False
    now = datetime.now().strftime("%H:%M")
    s, e = qm.get('start', '23:00'), qm.get('end', '07:00')
    return (now >= s or now <= e) if s > e else (s <= now <= e)

def send_msg(text, config, is_focus=False):
    # Telegram Push
    if config.get('push_tg_enabled') and config.get('tg_token'):
        params = urllib.parse.urlencode({"chat_id": config.get('tg_chat_id'), "text": text, "parse_mode": "Markdown"})
        try: urllib.request.urlopen(f"https://api.telegram.org/bot{config.get('tg_token')}/sendMessage?{params}", timeout=5)
        except: pass
    # WeChat (PushPlus) Push
    if config.get('push_wx_enabled') and config.get('wx_token'):
        title = "🌟 Focus Call" if is_focus else "🎙️ MMDVM Activity"
        data = json.dumps({
            "token": config.get('wx_token'), 
            "title": title, 
            "content": text.replace("\n", "<br>"), 
            "template": "html"
        }).encode('utf-8')
        try:
            req = urllib.request.Request("http://www.pushplus.plus/send", data=data, method='POST')
            req.add_header('Content-Type', 'application/json')
            urllib.request.urlopen(req, timeout=5)
        except: pass

def get_latest_log():
    files = glob.glob(os.path.join(LOG_DIR, "MMDVM-*.log"))
    return max(files, key=os.path.getmtime) if files else None

def main():
    print("🚀 MMDVM Push Service Started (Timezone Adaptive).")
    log_path = get_latest_log()
    if not log_path: return
    
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        f.seek(0, 2)
        while True:
            config = load_config()
            line = f.readline()
            if not line:
                time.sleep(0.5)
                # 检查日期变化（跨天）
                if get_latest_log() != log_path:
                    log_path = get_latest_log()
                    f = open(log_path, "r", encoding="utf-8", errors="ignore")
                continue
            
            # 监听通话结束行
            if "end of" in line and "transmission" in line:
                try:
                    # 1. 解析呼号和时长
                    call = re.search(r'from\s+([A-Z0-9/]+)', line).group(1).upper()
                    dur = float(re.search(r'(\d+\.?\d*)\s+seconds', line).group(1))
                    target = re.search(r'to\s+(TG\s*\d+|\d+)', line).group(1) if "to" in line else "Unknown"
                    
                    # 2. 时区自适应：解析日志时间戳并转为系统本地时间显示
                    t_match = re.search(r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}', line)
                    display_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) # 默认
                    if t_match:
                        log_ts = time.mktime(time.strptime(t_match.group(), "%Y-%m-%d %H:%M:%S"))
                        display_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(log_ts))

                    # 3. 过滤逻辑
                    focus_list = config.get('focus_list', [])
                    ignore_list = config.get('ignore_list', [])
                    is_focus = call in focus_list
                    
                    if focus_list and not is_focus: continue # 开启了关注列表但不在其中
                    if is_quiet_time(config) and not is_focus: continue # 静音时段且不是关注呼号
                    if dur < config.get('min_duration', 3.0): continue # 时长太短
                    if call == config.get('my_callsign') or call in ignore_list: continue # 自己或黑名单

                    # 4. 构建并发送消息
                    msg = f"*MMDVM Activity*\n---\n👤 Call: {call}\n👥 Target: {target}\n⏳ Dur: {dur}s\n⏰ Time: {display_time}"
                    send_msg(msg, config, is_focus)
                except Exception as e:
                    print(f"Error parsing line: {e}")

if __name__ == "__main__":
    main()
