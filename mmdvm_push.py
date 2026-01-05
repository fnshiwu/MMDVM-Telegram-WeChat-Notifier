import os, time, json, glob, re, urllib.request, urllib.parse, sys
from datetime import datetime
from threading import Thread

CONFIG_FILE = "/etc/mmdvm_push.json"
LOG_DIR = "/var/log/pi-star/"

# --- 预编译正则 (保持原逻辑) ---
RE_LINE_TYPE = re.compile(r'end of.*transmission', re.IGNORECASE)
RE_CALL = re.compile(r'from\s+([A-Z0-9/]+)')
RE_DUR = re.compile(r'(\d+\.?\d*)\s+seconds')
RE_TARGET = re.compile(r'to\s+(TG\s*\d+|PC\s*\d+|\d+)')

def async_post(url, data=None, is_json=False):
    def task():
        try:
            req = urllib.request.Request(url, data=data, method='POST') if data else urllib.request.Request(url)
            if is_json: req.add_header('Content-Type', 'application/json')
            with urllib.request.urlopen(req, timeout=5) as r:
                if "--test" in sys.argv: print("Success: Server accepted.")
        except Exception as e:
            if "--test" in sys.argv: print(f"Error: {e}")
    
    if "--test" in sys.argv: task()
    else: Thread(target=task, daemon=True).start()

def send_payload(config, type_label, body_text):
    # --- 严格恢复原始推送样式 ---
    msg_header = "━━━━━━━━━━━━━━━\n"
    
    # PushPlus (微信)
    if config.get('push_wx_enabled') and config.get('wx_token'):
        # 转换 Markdown 加粗为 HTML 标签以适配微信
        wx_body = body_text.replace("\n", "<br>").replace("**", "<b>").replace("**", "</b>")
        d = json.dumps({
            "token": config['wx_token'], 
            "title": f"{type_label}", 
            "content": f"<b>{type_label}</b><br>{wx_body}", 
            "template": "html"
        }).encode()
        async_post("http://www.pushplus.plus/send", data=d, is_json=True)
    
    # Telegram
    if config.get('push_tg_enabled') and config.get('tg_token'):
        params = urllib.parse.urlencode({
            "chat_id": config['tg_chat_id'], 
            "text": f"*{type_label}*\n{msg_header}{body_text}", 
            "parse_mode": "Markdown"
        })
        async_post(f"https://api.telegram.org/bot{config['tg_token']}/sendMessage?{params}")

def monitor():
    log_files = glob.glob(os.path.join(LOG_DIR, "MMDVM-*.log"))
    if not log_files: return
    current_log = max(log_files, key=os.path.getmtime)
    with open(current_log, "r", encoding="utf-8", errors="ignore") as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line: time.sleep(0.5); continue
            if RE_LINE_TYPE.search(line):
                try:
                    with open(CONFIG_FILE, 'r') as cf: conf = json.load(cf)
                    call = RE_CALL.search(line).group(1).upper()
                    dur = float(RE_DUR.search(line).group(1))
                    
                    # 过滤逻辑
                    if dur < conf.get('min_duration', 1.0) or call == conf.get('my_callsign'): continue
                    
                    is_cn = conf.get('ui_lang', 'cn') == 'cn'
                    type_label = "🎙️ 语音通联" if is_cn else "🎙️ Voice"
                    target = RE_TARGET.search(line).group(1) if RE_TARGET.search(line) else 'Unknown'
                    
                    # --- 推送正文内容还原 ---
                    body = f"👤 **呼号**: {call}\n👥 **群组**: {target}\n⏳ **时长**: {dur}秒"
                    
                    send_payload(conf, type_label, body)
                except: pass

if __name__ == "__main__":
    if "--test" in sys.argv:
        try:
            with open(CONFIG_FILE, 'r') as cf: c = json.load(cf)
            send_payload(c, "🔔 测试推送", "这是一条来自 Pi-Star 的测试消息，配置验证成功。")
        except Exception as e:
            print(f"Read Config Error: {e}")
    else:
        while True:
            try: monitor()
            except: time.sleep(5)
