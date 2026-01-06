import os, time, json, glob, re, urllib.request, urllib.parse, sys
from datetime import datetime, timezone, timedelta
from threading import Thread

# --- 路径对齐 PHP ---
CONFIG_FILE = "/etc/mmdvm_push.json"
LOG_DIR = "/var/log/pi-star/"
LOCAL_ID_FILE = "/usr/local/etc/DMRIds.dat"

LAST_MSG = {"call": "", "ts": 0}
HAM_CACHE = {} 

RE_VOICE = re.compile(r'end of (?:voice )?transmission', re.IGNORECASE)
RE_DATA = re.compile(r'end of data transmission', re.IGNORECASE)
RE_CALL = re.compile(r'from\s+([A-Z0-9/\-]+)')
RE_DUR = re.compile(r'(\d+\.?\d*)\s+seconds')
RE_TARGET = re.compile(r'to\s+([A-Z0-9/\-\s]+?)(?:,|$)', re.IGNORECASE)

def get_ham_info(callsign):
    """轻量化 grep 检索逻辑"""
    if callsign in HAM_CACHE: return HAM_CACHE[callsign]
    if os.path.exists(LOCAL_ID_FILE):
        try:
            cmd = f"grep -m 1 '\t{callsign}\t' {LOCAL_ID_FILE}"
            with os.popen(cmd) as p:
                result = p.read().strip()
                if result:
                    parts = result.split('\t')
                    if len(parts) >= 3:
                        name = parts[2].strip().upper()
                        city = parts[3].strip().title() if len(parts) > 3 else ""
                        country = parts[4].strip().upper() if len(parts) > 4 else ""
                        loc = f"{city}, {country}".strip(", ") if (city or country) else "Unknown"
                        info = {"name": f" ({name})", "loc": loc}
                        HAM_CACHE[callsign] = info
                        return info
        except: pass
    return {"name": "", "loc": "Unknown"}

def async_post(url, data=None, is_json=False):
    def task():
        try:
            req = urllib.request.Request(url, data=data, method='POST') if data else urllib.request.Request(url)
            if is_json: req.add_header('Content-Type', 'application/json')
            with urllib.request.urlopen(req, timeout=5) as r: pass
        except: pass
    Thread(target=task, daemon=True).start()

def send_payload(config, type_label, body_text):
    """已彻底清除 f-string 中的所有反斜杠"""
    msg_header = "━━━━━━━━━━━━━━━\n"
    if config.get('push_wx_enabled') and config.get('wx_token'):
        # 修复逻辑：不在 f-string 内做 replace
        br = "<br>"
        html_body = br.join(body_text.split("\n"))
        html_content = f"<b>{type_label}</b>{br}{html_body}"
        d = json.dumps({"token": config['wx_token'], "title": type_label, "content": html_content, "template": "html"}).encode()
        async_post("http://www.pushplus.plus/send", data=d, is_json=True)
    if config.get('push_tg_enabled') and config.get('tg_token'):
        params = urllib.parse.urlencode({"chat_id": config['tg_chat_id'], "text": f"*{type_label}*\n{msg_header}{body_text}", "parse_mode": "Markdown"})
        async_post(f"https://api.telegram.org/bot{config['tg_token']}/sendMessage?{params}")

def monitor():
    log_files = glob.glob(os.path.join(LOG_DIR, "MMDVM-*.log"))
    if not log_files: return
    current_log = max(log_files, key=os.path.getmtime)
    with open(current_log, "r", encoding="utf-8", errors="ignore") as f:
        f.seek(0, 2)
        while True:
            if datetime.now().strftime("%Y-%m-%d") not in current_log: return 
            line = f.readline()
            if not line:
                if os.path.getsize(current_log) < f.tell(): return
                time.sleep(0.5); continue
            is_v, is_d = RE_VOICE.search(line), RE_DATA.search(line)
            if is_v or is_d:
                try:
                    with open(CONFIG_FILE, 'r') as cf: conf = json.load(cf)
                    call_m = RE_CALL.search(line)
                    if not call_m: continue
                    call = call_m.group(1).upper()
                    curr_ts = time.time()
                    if call == LAST_MSG["call"] and (curr_ts - LAST_MSG["ts"]) < 3: continue
                    dur_m = RE_DUR.search(line)
                    dur = float(dur_m.group(1)) if dur_m else 0.0
                    if is_v and (dur < conf.get('min_duration', 1.0) or call == conf.get('my_callsign')): continue
                    LAST_MSG["call"], LAST_MSG["ts"] = call, curr_ts
                    info = get_ham_info(call)
                    slot = 'Slot 1' if 'Slot 1' in line else 'Slot 2'
                    type_label = f"🎙️ 语音 ({slot})" if is_v else f"💾 数据 ({slot})"
                    target = RE_TARGET.search(line).group(1).strip() if RE_TARGET.search(line) else 'Unknown'
                    body = (f"👤 **呼号**: {call}{info['name']}\n👥 **群组**: {target}\n📍 **地区**: {info['loc']}\n"
                            f"📅 **日期**: {datetime.now().strftime('%Y-%m-%d')}\n⏰ **时间**: {datetime.now().strftime('%H:%M:%S')}\n⏳ **时长**: {dur}秒")
                    send_payload(conf, type_label, body)
                except: pass

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        try:
            with open(CONFIG_FILE, 'r') as cf: c = json.load(cf)
            send_payload(c, "🔔 测试推送 (V2.82)", "路径与语法校验成功！")
            # 必须 print 这一句，PHP 才能捕获到反馈并停止“转圈”
            print("Success: Test packet sent.")
            time.sleep(1) 
        except Exception as e:
            print(f"Error: {e}")
    else:
        while True:
            try: monitor()
            except: time.sleep(5)
