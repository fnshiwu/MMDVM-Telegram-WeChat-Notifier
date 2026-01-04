既然你的项目已经实现了从**后端监控**、**前端原生 UI 管理**到**一键安装脚本**的全栈功能，我们需要一份高质量的 GitHub `README.md` 来提升专业度。

这份教程采用了中英文双语架构，重点突出了**一键安装**和**原生集成**。

---

# 🎙️ MMDVM Telegram & WeChat Notifier

[English Version](https://www.google.com/search?q=%23english-guide) | [中文说明](https://www.google.com/search?q=%23chinese-guide)

---

<a name="chinese-guide"></a>

## 🇨🇳 中文说明

这是一个为 **Pi-Star** 热点板深度定制的通联实时推送工具。它能够自动监控 MMDVM 日志，识别语音与数据通联，并通过 Telegram 或微信（PushPlus）将精美格式的消息推送到您的手机。

### ✨ 核心亮点

* **原生 UI 集成**：管理页面完美适配 Pi-Star 红黑配色风格，直接集成在后台菜单。
* **智能识别**：自动区分 `🎙️ 话音通联` 与 `📟 数据业务`。
* **实时状态**：管理界面内置服务状态灯，实时显示监控进程是否正常。
* **时区补偿**：自动将日志的 UTC 时间转换为 **北京时间** 进行推送。
* **开箱即用**：提供一键安装指令，自动处理权限、依赖与菜单挂载。

### 🚀 快速安装

在 Pi-Star 终端（SSH）中，直接复制并运行以下命令：

```bash
rpi-rw && cd /home/pi-star && git clone https://github.com/fnshiwu/MMDVM-Telegram-WeChat-Notifier.git && cd MMDVM-Telegram-WeChat-Notifier && chmod +x install.sh && sed -i 's/\r$//' install.sh && sudo ./install.sh

```

### ⚙️ 使用说明

1. 安装完成后，刷新 Pi-Star 管理后台页面。
2. 在顶部菜单点击 **[推送设置]**（或手动访问 `http://你的IP/admin/push_admin.php`）。
3. 填写您的呼号、TG Token 或微信 Token。
4. 点击 **保存设置**，推送服务将自动生效。

---

<a name="english-guide"></a>

## 🇺🇸 English Guide

A professional real-time notification tool for **Pi-Star** hotspots. It monitors MMDVM logs and sends formatted alerts to **Telegram** or **WeChat** (via PushPlus).

### 🌟 Key Features

* **Native UI**: Seamlessly integrates into the Pi-Star admin panel with a matching theme.
* **Smart Recognition**: Distinguishes between `🎙️ Voice Transmission` and `📟 Data Service`.
* **Live Status**: Built-in service indicator to monitor the background process.
* **Timezone Support**: Automatically adjusts UTC log timestamps to local time.
* **One-Click Deployment**: Automates dependency installation, permissions, and menu injection.

### 📦 Installation

Run the following command in your Pi-Star terminal via SSH:

```bash
rpi-rw && cd /home/pi-star && git clone https://github.com/fnshiwu/MMDVM-Telegram-WeChat-Notifier.git && cd MMDVM-Telegram-WeChat-Notifier && chmod +x install.sh && sed -i 's/\r$//' install.sh && sudo ./install.sh

```

---

## 📂 仓库结构 (Repository Structure)

| 文件 (File) | 描述 (Description) |
| --- | --- |
| `push_script.py` | 后端 Python 监控脚本，负责正则解析与 API 发送 |
| `push_admin.php` | 前端 PHP 管理界面，提供原生风格的配置表单 |
| `install.sh` | 自动化集成脚本，负责菜单注入与服务配置 |
| `mmdvm-push.service` | Systemd 守护进程，确保程序开机自启 |

---

## 🛠️ 常见问题排查 (Troubleshooting)

* **没有推送？**
1. 请确保在网页端填写的“我的呼号”与实际发射呼号一致（脚本默认不推送自己的发射）。
2. 使用 `sudo journalctl -u mmdvm-push.service -f` 检查实时运行日志。


* **管理页面报 403 错误？**
执行 `sudo chown www-data:www-data /var/www/dashboard/admin/push_admin.php` 修复权限。
* **无法保存配置？**
执行 `sudo chmod 666 /etc/mmdvm_push.json`。

---

## 🤝 贡献 (Contribution)

欢迎通过 Pull Request 提交更好的正则匹配规则或 UI 改进方案。

**73! de BA4SMQ**

---
