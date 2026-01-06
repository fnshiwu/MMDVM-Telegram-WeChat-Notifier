import os, time, json, glob, re, urllib.request, urllib.parse, sys
from datetime import datetime, timezone, timedelta
from threading import Thread

# --- 配置路径 ---
CONFIG_FILE = "/etc/mmdvm_push.json"
LOG_DIR = "/var/log/pi-star/"
LOCAL_ID_FILE = "/usr/local/etc/DMRIds.dat"

# --- 全局内存缓存 ---
LAST_MSG = {"call": "", "ts": 0}  # 防抖缓存
HAM_CACHE = {}                    # 呼号信息缓存 (启动时加载本地库)

# --- 预编译正则 ---
RE_VOICE = re.compile(r'end of (?:voice )?transmission', re.IGNORECASE)
RE_DATA = re.compile(r'end of data transmission', re.IGNORECASE)
RE_CALL = re.compile(r'from\s+([A-Z0-9/\-]+)')
RE_DUR = re.compile(r'(\d+\.?\d*)\s+seconds')
RE_TARGET = re.compile(r'to\s+([A-Z0-9/\-\s]+?)(?:,|$)', re.IGNORECASE)
RE_TIME = re.compile(r'\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}')

def load_local_dmr_ids():
    """解析本地 DMRIds.dat 库：DMRID | CALL | NAME | CITY | COUNTRY"""
    ids_map = {}
    if not os.path.exists(LOCAL_ID_FILE):
        return ids_map
    try:
        with open(LOCAL_ID_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if line.startswith('#') or len(line) < 5: continue
                # Pi-Star 标准格式通常以 Tab 分隔
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    call = parts[1].upper()
                    name = parts[2].strip().upper() if len(parts) > 2 else ""
                    city = parts[3].strip().title() if len(parts) > 3 else ""
                    country = parts[4].strip().upper() if len(parts) > 4 else ""
                    
                    ids_map[call] = {
                        "name": f" ({name})" if name else "",
                        "location": f"{city}, {country}".strip(", ") if (city or country) else "Unknown"
                    }
    except: pass
    return ids_map

def get_ham_info(callsign):
    """混合查询：内存(本地库)优先 -> API 后备"""
    # 1. 尝试从已加载的本地库或缓存读取
    if callsign in HAM_CACHE:
        return HAM_CACHE[callsign]
    
    # 2. 如果本地库没搜到，尝试在线 API (针对新呼号)
    try:
        api_url = f"https://radioid.net/api/dmr/user/?callsign={callsign}"
        with urllib.request.urlopen(api_url, timeout=2) as r:
            res = json.loads(r.read().decode())
            if res and res.get("results"):
                user = res["results"][0]
                name = user.get('fname', '').upper()
                city = user.get('city', '').title()
                country = user.get('country', '').upper()
                info = {
                    "name": f" ({name})" if name else "",
                    "location": f"{city}, {country}".strip(", ") if city else country
                }
                HAM_CACHE[callsign] = info
                return info
    except: pass
    
    # 3. 全部失败，标记为 Unknown 避免重复请求
    res_null = {"name": "", "location": "Unknown"}
    HAM_CACHE[callsign] = res_null
    return res_null

def async_post(url, data=None, is_json=False):
    def task():
        try:
            req = urllib.request.Request(url, data=data, method='POST') if data else urllib.request.Request(url)
            if is_json: req.add_header('Content-Type', 'application/json')
            with urllib.request.urlopen(req, timeout=3) as r: pass
        except: pass
    Thread(target=task, daemon=True).start()

def send_payload(config, type_label, body_text):
    msg_header = "━━━━━━━━━━━━━━━\n"
    if config.get('push_wx_enabled') and config.get('wx_token'):
        wx_body = body_text.replace("\n", "<br>").replace("**", "<b>").replace("**", "</b>")
        d = json.dumps({"token": config['wx_token'], "title": type_label, 
                        "content": f"<b>{type_label}</b><br>{wx_body}", "template": "html"}).encode()
        async_post("http://www.pushplus.plus/send", data=d, is_json=True)
    
    if config.get('push_tg_enabled') and config.get('tg_token'):
        params = urllib.parse.urlencode({"chat_id": config['tg_chat_id'], 
                                         "text": f"*{type_label}*\n{msg_header}{body_text}", "parse_mode": "Markdown"})
        async_post(f"https://api.telegram.org/bot{config['tg_token']}/sendMessage?{params}")

def monitor():
    log_files = glob.glob(os.path.join(LOG_DIR, "MMDVM-*.log"))
    if not log_files: return
    current_log = max(log_files, key=os.path.getmtime)
    
    with open(current_log, "r", encoding="utf-8", errors="ignore") as f:
        f.seek(0, 2)
        while True:
            # 跨天自愈检测
            if datetime.now().strftime("%Y-%m-%d") not in current_log: return 

            line = f.readline()
            if not line:
                if os.path.getsize(current_log) < f.tell(): return
                time.sleep(0.5); continue
            
            is_v = RE_VOICE.search(line)
            is_d = RE_DATA.search(line)
            
            if is_v or is_d:
                try:
                    with open(CONFIG_FILE, 'r') as cf: conf = json.load(cf)
                    call_m = RE_CALL.search(line)
                    if not call_m: continue
                    call = call_m.group(1).upper()
                    
                    # 防抖去重逻辑
                    curr_ts = time.time()
                    if call == LAST_MSG["call"] and (curr_ts - LAST_MSG["ts"]) < 3: continue
                    
                    dur_m = RE_DUR.search(line)
                    dur = float(dur_m.group(1)) if dur_m else 0.0
                    if is_v and (dur < conf.get('min_duration', 1.0) or call == conf.get('my_callsign')): continue
                    
                    LAST_MSG["call"], LAST_MSG["ts"] = call, curr_ts
                    
                    # 获取个人资料 (优先本地)
                    info = get_ham_info(call)
                    
                    # 处理时间
                    t_m = RE_TIME.search(line)
                    now = datetime.now()
                    date_str, time_str = now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")
                    if t_m:
                        utc_t = datetime.strptime(t_m.group(), "%Y-%m-%d %H:%M:%S")
                        local_t = utc_t.replace(tzinfo=timezone.utc).astimezone(tz=None)
                        date_str, time_str = local_t.strftime("%Y-%m-%d"), local_t.strftime("%H:%M:%S")
                    
                    # 样式封装
                    slot = 'Slot 1' if 'Slot 1' in line else 'Slot 2'
                    is_cn = conf.get('ui_lang', 'cn') == 'cn'
                    v_label = f"🎙️ 语音通联 ({slot})" if is_cn else f"🎙️ Voice ({slot})"
                    d_label = f"💾 数据传输 ({slot})" if is_cn else f"💾 Data ({slot})"
                    type_label = v_label if is_v else d_label
                    
                    target_m = RE_TARGET.search(line)
                    target = target_m.group(1).strip() if target_m else 'Unknown'
                    
                    body = (f"👤 **呼号**: {call}{info['name']}\n"
                            f"👥 **群组**: {target}\n"
                            f"📍 **地区**: {info['location']}\n"
                            f"📅 **日期**: {date_str}\n"
                            f"⏰ **时间**: {time_str}\n"
                            f"⏳ **时长**: {dur}秒")
                    
                    send_payload(conf, type_label, body)
                except: pass

if __name__ == "__main__":
    # 启动时加载本地库
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 正在加载本地呼号库...")
    HAM_CACHE = load_local_dmr_ids()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 成功加载 {len(HAM_CACHE)} 条记录，开始监控。")
    
    while True:
        try: monitor()
        except: time.sleep(5)
