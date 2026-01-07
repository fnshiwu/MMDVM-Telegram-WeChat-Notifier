import os, time, json, glob, re, urllib.request, urllib.parse, sys, base64, hmac, hashlib, mmap
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from threading import Semaphore

# --- 路径与常量配置 ---
CONFIG_FILE = "/etc/mmdvm_push.json"
LOG_DIR = "/var/log/pi-star/"
# 替换为 CSV 文件路径
LOCAL_ID_FILE = "/usr/local/etc/nextionUsers.csv"

class ConfigManager:
    """配置管理器：支持热加载，减少IO操作"""
    _config = {}
    _last_mtime = 0
    _check_interval = 5  # 每5秒检查一次文件变化
    _last_check_time = 0

    @classmethod
    def get_config(cls):
        now = time.time()
        if now - cls._last_check_time < cls._check_interval:
            return cls._config

        cls._last_check_time = now
        if not os.path.exists(CONFIG_FILE):
            return {}
            
        try:
            mtime = os.path.getmtime(CONFIG_FILE)
            if mtime > cls._last_mtime:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    cls._config = json.load(f)
                cls._last_mtime = mtime
        except Exception as e:
            print(f"配置读取失败: {e}")
        
        return cls._config

class HamInfoManager:
    """处理呼号信息查询与缓存 (已适配 CSV 并增加国家/国旗转换)"""
    
   # 完整全球国家/地区映射表 (适配 nextionUsers.csv)
    COUNTRY_MAP = {
        # 亚洲 (Asia)
        "China": "🇨🇳 中国", "Hong Kong": "🇭🇰 中国香港", "Macao": "🇲🇴 中国澳门", "Taiwan": "🇹🇼 中国台湾",
        "Japan": "🇯🇵 日本", "Korea": "🇰🇷 韩国", "South Korea": "🇰🇷 韩国", "North Korea": "🇰🇵 朝鲜",
        "Thailand": "🇹🇭 泰国", "Singapore": "🇸🇬 新加坡", "Malaysia": "🇲🇾 马来西亚", "Indonesia": "🇮🇩 印度尼西亚",
        "Philippines": "🇵🇭 菲律宾", "Vietnam": "🇻🇳 越南", "India": "🇮🇳 印度", "Pakistan": "🇵🇰 巴基斯坦",
        "Sri Lanka": "🇱🇰 斯里兰卡", "Bangladesh": "🇧🇩 孟加拉国", "Nepal": "🇳🇵 尼泊尔", "Mongolia": "🇲🇳 蒙古",
        "United Arab Emirates": "🇦🇪 阿联酋", "UAE": "🇦🇪 阿联酋", "Saudi Arabia": "🇸🇦 沙特", "Israel": "🇮🇱 以色列",
        "Turkey": "🇹🇷 土耳其", "Iran": "🇮🇷 伊朗", "Iraq": "🇮🇶 伊拉克", "Kuwait": "🇰🇼 科威特",
        "Oman": "🇴🇲 阿曼", "Qatar": "🇶🇦 卡塔尔", "Jordan": "🇯🇴 约旦", "Lebanon": "🇱🇧 黎巴嫩",
        "Kazakhstan": "🇰🇿 哈萨克斯坦", "Uzbekistan": "🇺🇿 乌兹别克斯坦",

        # 欧洲 (Europe)
        "United Kingdom": "🇬🇧 英国", "UK": "🇬🇧 英国", "England": "🇬🇧 英国", "Germany": "🇩🇪 德国",
        "France": "🇫🇷 法国", "Italy": "🇮🇹 意大利", "Spain": "🇪🇸 西班牙", "Portugal": "🇵🇹 葡萄牙",
        "Russia": "🇷🇺 俄罗斯", "Russian Federation": "🇷🇺 俄罗斯", "Netherlands": "🇳🇱 荷兰",
        "Belgium": "🇧🇪 比利时", "Switzerland": "🇨🇭 瑞士", "Austria": "🇦🇹 奥地利", "Sweden": "🇸🇪 瑞典",
        "Norway": "🇳🇴 挪威", "Denmark": "🇩🇰 丹麦", "Finland": "🇫🇮 芬兰", "Poland": "🇵🇱 波兰",
        "Czech Republic": "🇨🇿 捷克", "Hungary": "🇭🇺 匈牙利", "Greece": "🇬🇷 希腊", "Ireland": "🇮🇪 爱尔兰",
        "Romania": "🇷🇴 罗马尼亚", "Bulgaria": "🇧🇬 保加利亚", "Ukraine": "🇺🇦 乌克兰", "Belarus": "🇧🇾 白俄罗斯",
        "Slovakia": "🇸🇰 斯洛伐克", "Croatia": "🇭🇷 克罗地亚", "Serbia": "🇷🇸 塞尔维亚", "Slovenia": "🇸🇮 斯洛文尼亚",
        "Estonia": "🇪🇪 爱沙尼亚", "Latvia": "🇱🇻 拉脱维亚", "Lithuania": "🇱🇹 立陶宛", "Iceland": "🇮🇸 冰岛",
        "Luxembourg": "🇱🇺 卢森堡", "Monaco": "🇲🇨 摩纳哥", "Cyprus": "🇨🇾 塞浦路斯", "Malta": "🇲🇹 马耳他",

        # 北美洲 (North America)
        "United States": "🇺🇸 美国", "USA": "🇺🇸 美国", "Canada": "🇨🇦 加拿大", "Mexico": "🇲🇽 墨西哥",
        "Cuba": "🇨🇺 古巴", "Jamaica": "🇯🇲 牙买加", "Puerto Rico": "🇵🇷 波多黎各", "Dominican Republic": "🇩🇴 多米尼加",
        "Costa Rica": "🇨🇷 哥斯达黎加", "Panama": "🇵🇦 巴拿马", "Guatemala": "🇬🇹 危地马拉", "Honduras": "🇭🇳 洪都拉斯",

        # 南美洲 (South America)
        "Brazil": "🇧🇷 巴西", "Argentina": "🇦🇷 阿根廷", "Chile": "🇨🇱 智利", "Colombia": "🇨🇴 哥伦比亚",
        "Peru": "🇵🇪 秘鲁", "Venezuela": "🇻🇪 委内瑞拉", "Uruguay": "🇺🇾 乌拉圭", "Paraguay": "🇵🇾 巴拉圭",
        "Ecuador": "🇪🇨 厄瓜多尔", "Bolivia": "🇧🇴 玻利维亚",

        # 大洋洲 (Oceania)
        "Australia": "🇦🇺 澳大利亚", "New Zealand": "🇳🇿 新西兰", "Fiji": "🇫🇯 斐济", "Papua New Guinea": "🇵🇬 巴布亚新几内亚",

        # 非洲 (Africa)
        "South Africa": "🇿🇦 南非", "Egypt": "🇪🇬 埃及", "Nigeria": "🇳🇬 尼日利亚", "Kenya": "🇰🇪 肯尼亚",
        "Morocco": "🇲🇦 摩洛哥", "Algeria": "🇩🇿 阿尔及利亚", "Ethiopia": "🇪🇹 埃塞俄比亚", "Ghana": "🇬🇭 加纳",
        "Tanzania": "🇹🇿 坦桑尼亚", "Uganda": "🇺🇬 乌干达", "Mauritius": "🇲🇺 毛里求斯", "Seychelles": "🇸🇨 塞舌尔"
    }

    def __init__(self, id_file):
        self.id_file = id_file
        self._io_lock = Semaphore(4)

    @lru_cache(maxsize=4096)
    def get_info(self, callsign):
        if not os.path.exists(self.id_file):
            return {"name": "", "loc": "Unknown"}

        if not self._io_lock.acquire(timeout=2):
            return {"name": "", "loc": "Unknown"}

        try:
            with open(self.id_file, 'rb') as f:
                try:
                    with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                        # 替换：CSV 通常呼号两端有逗号
                        query = f",{callsign},".encode('utf-8')
                        idx = mm.find(query)
                        
                        if idx != -1:
                            start = mm.rfind(b'\n', 0, idx) + 1
                            end = mm.find(b'\n', idx)
                            if end == -1: end = len(mm)
                            
                            line = mm[start:end].decode('utf-8', 'ignore')
                            # 替换：使用逗号分隔
                            parts = line.split(',')
                            
                            # 提取 CSV 信息 (0:ID, 1:CALL, 2:名, 3:姓, 4:城市, 5:省, 6:国家)
                            first_name = parts[2].strip() if len(parts) > 2 else ""
                            last_name = parts[3].strip() if len(parts) > 3 else ""
                            city = parts[4].strip().title() if len(parts) > 4 else ""
                            state = parts[5].strip().upper() if len(parts) > 5 else ""
                            raw_country = parts[6].strip() if len(parts) > 6 else "Unknown"
                            
                            # 转换国家名
                            country_display = self.COUNTRY_MAP.get(raw_country, f"🏳️ {raw_country}")
                            
                            full_name = f"{first_name} {last_name}".strip().upper()
                            loc = f"{city}, {state} ({country_display})"
                            
                            return {"name": f" ({full_name})", "loc": loc}
                except ValueError:
                    pass
        except Exception as e:
            print(f"查询异常: {e}")
        finally:
            self._io_lock.release()
            
        return {"name": "", "loc": "Unknown"}

class PushService:
    """管理多平台推送逻辑 (保持原逻辑)"""
    _executor = ThreadPoolExecutor(max_workers=3)

    @staticmethod
    def get_fs_sign(secret, timestamp):
        string_to_sign = f'{timestamp}\n{secret}'
        hmac_code = hmac.new(string_to_sign.encode("utf-8"), digestmod=hashlib.sha256).digest()
        return base64.b64encode(hmac_code).decode('utf-8')

    @classmethod
    def post_request(cls, url, data=None, is_json=False):
        try:
            req = urllib.request.Request(url, data=data, method='POST') if data else urllib.request.Request(url)
            if is_json: req.add_header('Content-Type', 'application/json; charset=utf-8')
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.read().decode()
        except Exception as e:
            print(f"推送网络错误: {e}")
            return None

    @classmethod
    def _do_send_task(cls, config, type_label, body_text, is_voice):
        try:
            msg_header = "━━━━━━━━━━━━━━━\n"
            if config.get('push_wx_enabled') and config.get('wx_token'):
                br = "<br>"
                html_content = f"<b>{type_label}</b>{br}{br.join(body_text.splitlines())}"
                d = json.dumps({"token": config['wx_token'], "title": type_label, "content": html_content, "template": "html"}).encode()
                cls.post_request("http://www.pushplus.plus/send", data=d, is_json=True)
            
            if config.get('push_tg_enabled') and config.get('tg_token'):
                params = urllib.parse.urlencode({"chat_id": config['tg_chat_id'], "text": f"*{type_label}*\n{msg_header}{body_text}", "parse_mode": "Markdown"})
                cls.post_request(f"https://api.telegram.org/bot{config['tg_token']}/sendMessage?{params}")
            
            if config.get('push_fs_enabled') and config.get('fs_webhook'):
                ts = str(int(time.time()))
                fs_payload = {"msg_type": "interactive", "card": {"header": {"title": {"tag": "plain_text", "content": type_label}, "template": "blue" if is_voice else "green"}, "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": body_text}}]}}
                if config.get('fs_secret'):
                    fs_payload["timestamp"], fs_payload["sign"] = ts, cls.get_fs_sign(config['fs_secret'], ts)
                cls.post_request(config['fs_webhook'], data=json.dumps(fs_payload).encode(), is_json=True)
        except Exception as e:
            print(f"推送任务异常: {e}")

    @classmethod
    def send(cls, config, type_label, body_text, is_voice=True, async_mode=True):
        if async_mode:
            cls._executor.submit(cls._do_send_task, config, type_label, body_text, is_voice)
        else:
            cls._do_send_task(config, type_label, body_text, is_voice)

class MMDVMMonitor:
    """核心监控类 (保持原逻辑)"""
    def __init__(self):
        self.last_msg = {"call": "", "ts": 0}
        self.ham_manager = HamInfoManager(LOCAL_ID_FILE)
        self.re_master = re.compile(
            r'end of (?P<v_type>(?:voice )?|data )transmission from '
            r'(?P<call>[A-Z0-9/\-]+) to (?P<target>[A-Z0-9/\-\s]+?), '
            r'(?P<dur>\d+\.?\d*) seconds, '
            r'(?P<loss>\d+)% packet loss, '
            r'BER: (?P<ber>\d+\.?\d*)%', 
            re.IGNORECASE
        )

    def is_quiet_time(self, conf):
        if not conf.get('quiet_mode', {}).get('enabled'): return False
        now = datetime.now().strftime("%H:%M")
        start, end = conf['quiet_mode']['start'], conf['quiet_mode']['end']
        return (start <= now <= end) if start <= end else (now >= start or now <= end)

    def get_latest_log(self):
        try:
            log_files = [f for f in glob.glob(os.path.join(LOG_DIR, "MMDVM-*.log")) if os.path.getsize(f) > 0]
            return max(log_files, key=os.path.getmtime) if log_files else None
        except Exception:
            return None

    def run(self):
        print(f"MMDVM 监控启动成功，正在读取 CSV 数据库...")
        while True:
            try:
                current_log = self.get_latest_log()
                if not current_log:
                    time.sleep(5); continue
                
                with open(current_log, "r", encoding="utf-8", errors="ignore") as f:
                    f.seek(0, 2)
                    last_rotation_check = time.time()
                    while True:
                        if time.time() - last_rotation_check > 5:
                            new_log = self.get_latest_log()
                            if new_log and new_log != current_log: break
                            last_rotation_check = time.time()

                        line = f.readline()
                        if not line:
                            time.sleep(0.1)
                            continue
                        self.process_line(line)
            except Exception as e:
                print(f"运行异常: {e}"); time.sleep(5)

    def process_line(self, line):
        if "end of" not in line.lower(): return
        match = self.re_master.search(line)
        if not match: return

        try:
            conf = ConfigManager.get_config()
            if not conf: return

            v_type_raw = match.group('v_type').lower()
            is_v = 'data' not in v_type_raw
            call = match.group('call').upper()
            target = match.group('target').strip()
            dur = float(match.group('dur'))
            loss = int(match.group('loss'))
            ber = float(match.group('ber'))

            if self.is_quiet_time(conf): return
            if call in conf.get('ignore_list', []): return
            if conf.get('focus_list') and call not in conf['focus_list']: return
            
            curr_ts = time.time()
            if call == self.last_msg["call"] and (curr_ts - self.last_msg["ts"]) < 3: return
            if is_v and (dur < conf.get('min_duration', 1.0) or call == conf.get('my_callsign')): return
            
            self.last_msg.update({"call": call, "ts": curr_ts})
            info = self.ham_manager.get_info(call)
            slot = "Slot 1" if "Slot 1" in line else "Slot 2"
            
            type_label = f"🎙️ 语音通联 ({slot})" if is_v else f"💾 数据模式 ({slot})"
            body = (f"👤 **呼号**: {call}{info['name']}\n"
                    f"👥 **群组**: {target}\n"
                    f"📍 **地区**: {info['loc']}\n"
                    f"📅 **日期**: {datetime.now().strftime('%Y-%m-%d')}\n"
                    f"⏰ **时间**: {datetime.now().strftime('%H:%M:%S')}\n"
                    f"⏳ **时长**: {dur}秒\n"
                    f"📦 **丢失**: {loss}%\n"
                    f"📉 **误码**: {ber}%")
            
            PushService.send(conf, type_label, body, is_voice=is_v, async_mode=True)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 匹配成功: {call} | {info['loc']}")
            
        except Exception as e:
            print(f"解析错误: {e}")

if __name__ == "__main__":
    monitor = MMDVMMonitor()
    monitor.run()
