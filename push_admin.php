<?php
// 1. 获取 Pi-Star 核心配置，精准定位语言设置
$pistarConfig = [];
if (file_exists('/etc/pistar-css.php')) {
    $pistarConfig = parse_ini_file('/etc/pistar-css.php');
}
// 读取“常规配置”中的仪表盘语言，默认为 english
$current_lang = isset($pistarConfig['pistar_language']) ? strtolower($pistarConfig['pistar_language']) : 'english';

// 2. 挂载系统原生语言包
$lang_file = '/var/www/dashboard/lang/'.$current_lang.'.php';
if (file_exists($lang_file)) {
    include_once($lang_file);
} else {
    include_once('/var/www/dashboard/lang/english.php'); // 找不到则回退到英语
}

// 3. 插件自定义词条翻译 (基于 $current_lang)
$is_cn = (strpos($current_lang, 'chinese') !== false);
$txt_push_title  = $is_cn ? "推送功能设置" : "Push Notifier Settings";
$txt_core_cfg    = $is_cn ? "核心配置" : "Core Configuration";
$txt_my_call     = $is_cn ? "我的呼号" : "My Callsign";
$txt_tg_cfg      = $is_cn ? "Telegram 推送设置" : "Telegram Settings";
$txt_wx_cfg      = $is_cn ? "微信 (PushPlus) 设置" : "WeChat (PushPlus) Settings";
$txt_filter_cfg  = $is_cn ? "黑白名单管理 (每行一个呼号)" : "Filter Lists (One per line)";
$txt_ignore      = $is_cn ? "忽略列表" : "Ignore List";
$txt_focus       = $is_cn ? "关注列表" : "Focus List";
$txt_quiet_cfg   = $is_cn ? "静音时段 (Quiet Mode)" : "Quiet Mode Range";
$txt_save_btn    = $is_cn ? "保存所有设置" : "Save Settings";
$txt_test_btn    = $is_cn ? "发送测试推送" : "Send Test Push";
$txt_back_btn    = $is_cn ? "返回" : "Back";
$txt_enabled     = isset($lang['enabled']) ? $lang['enabled'] : ($is_cn ? "启用" : "Enabled");

// 4. 数据处理与文件保存
$configFile = '/etc/mmdvm_push.json';
$config = json_decode(file_get_contents($configFile), true);
$alertMsg = ""; 

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'];
    if ($action === 'save') {
        $config['my_callsign'] = strtoupper(trim($_POST['callsign']));
        $config['push_tg_enabled'] = isset($_POST['tg_en']);
        $config['tg_token'] = trim($_POST['tg_token']);
        $config['tg_chat_id'] = trim($_POST['tg_chat_id']);
        $config['push_wx_enabled'] = isset($_POST['wx_en']);
        $config['wx_token'] = trim($_POST['wx_token']);
        $config['ignore_list'] = array_filter(array_map('trim', explode("\n", strtoupper($_POST['ignore_list']))));
        $config['focus_list'] = array_filter(array_map('trim', explode("\n", strtoupper($_POST['focus_list']))));
        $config['quiet_mode']['enabled'] = isset($_POST['qm_en']);
        $config['quiet_mode']['start_time'] = $_POST['qm_start'];
        $config['quiet_mode']['end_time'] = $_POST['qm_end'];
        file_put_contents($configFile, json_encode($config, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
        $alertMsg = $is_cn ? "设置保存成功！" : "Settings Saved!";
    }
    if ($action === 'test') {
        $test_msg = "🔔 MMDVM 推送测试成功！\n呼号: " . ($_POST['callsign'] ?: "BA4SMQ") . "\n时间: " . date("H:i:s");
        if (isset($_POST['tg_en'])) @file_get_contents("https://api.telegram.org/bot".trim($_POST['tg_token'])."/sendMessage?chat_id=".trim($_POST['tg_chat_id'])."&text=".urlencode($test_msg));
        if (isset($_POST['wx_en'])) @file_get_contents("http://www.pushplus.plus/send?token=".trim($_POST['wx_token'])."&title=Test&content=".urlencode($test_msg));
        $alertMsg = $is_cn ? "测试消息已发出！" : "Test message sent!";
    }
}
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link rel="stylesheet" type="text/css" media="screen and (min-width: 830px)" href="css/pistar-css.php?version=0.95" />
    <link rel="stylesheet" type="text/css" media="screen and (max-width: 829px)" href="css/pistar-css-mini.php?version=0.95" />
    <title><?php echo $txt_push_title; ?></title>
    <style type="text/css">
        textarea { width: 98%; height: 60px; font-family: "Lucida Console", Monaco, monospace; font-size: 12px; border: 1px solid #666; }
        input[type="text"], input[type="password"], input[type="time"] { width: 95%; border: 1px solid #666; }
    </style>
    <script type="text/javascript">
        <?php if ($alertMsg) { echo "alert('$alertMsg');"; } ?>
    </script>
</head>
<body>
<div class="container">
    <div class="header">
        <div style="font-size: 8px; text-align: left; padding-left: 8px; float: left;">Hostname: <?php echo exec('hostname'); ?></div>
        <div style="font-size: 8px; text-align: right; padding-right: 8px;">Pi-Star: <?php echo exec('cat /etc/pistar-release | cut -d" " -f3'); ?></div>
        <h1><?php echo $lang['dashboard']." - ".exec('hostname'); ?></h1>
        
        <p style="padding-right: 5px; text-align: right; color: #ffffff;"> 
            <a href="/" style="color: #ffffff;"><?php echo $lang['dashboard']; ?></a> | 
            <a href="/admin/" style="color: #ffffff;"><?php echo $lang['admin']; ?></a> | 
            <a href="/admin/live_modem_log.php" style="color: #ffffff;"><?php echo $lang['live_logs']; ?></a> | 
            <a href="/admin/power.php" style="color: #ffffff;"><?php echo $lang['power']; ?></a> | 
            <a href="/admin/update.php" style="color: #ffffff;"><?php echo $lang['update']; ?></a> | 
            <a href="/admin/push_admin.php" style="color: #ffffff; font-weight: bold;"><?php echo $txt_push_title; ?></a> | 
            <a href="/admin/configure.php" style="color: #ffffff;"><?php echo $lang['configuration']; ?></a>
        </p>
    </div>

    <div class="contentwide">
        <form method="post">
        <table class="settings">
            <thead>
                <tr><th colspan="2"><?php echo $txt_push_title; ?></th></tr>
            </thead>
            <tbody>
                <tr>
                    <td align="right" width="35%"><?php echo $txt_my_call; ?>:</td>
                    <td align="left"><input type="text" name="callsign" value="<?php echo $config['my_callsign'];?>" /></td>
                </tr>

                <tr><th colspan="2"><?php echo $txt_tg_cfg; ?></th></tr>
                <tr><td align="right"><?php echo $txt_enabled; ?>:</td><td align="left"><input type="checkbox" name="tg_en" <?php if($config['push_tg_enabled']) echo "checked";?> /></td></tr>
                <tr><td align="right">Bot Token:</td><td align="left"><input type="password" name="tg_token" value="<?php echo $config['tg_token'];?>" /></td></tr>
                <tr><td align="right">Chat ID:</td><td align="left"><input type="text" name="tg_chat_id" value="<?php echo $config['tg_chat_id'];?>" /></td></tr>

                <tr><th colspan="2"><?php echo $txt_wx_cfg; ?></th></tr>
                <tr><td align="right"><?php echo $txt_enabled; ?>:</td><td align="left"><input type="checkbox" name="wx_en" <?php if($config['push_wx_enabled']) echo "checked";?> /></td></tr>
                <tr><td align="right">Token:</td><td align="left"><input type="password" name="wx_token" value="<?php echo $config['wx_token'];?>" /></td></tr>

                <tr><th colspan="2"><?php echo $txt_filter_cfg; ?></th></tr>
                <tr><td align="right"><?php echo $txt_ignore; ?>:</td><td align="left"><textarea name="ignore_list"><?php echo implode("\n", $config['ignore_list']);?></textarea></td></tr>
                <tr><td align="right"><?php echo $txt_focus; ?>:</td><td align="left"><textarea name="focus_list"><?php echo implode("\n", $config['focus_list']);?></textarea></td></tr>

                <tr><th colspan="2"><?php echo $txt_quiet_cfg; ?></th></tr>
                <tr><td align="right"><?php echo $txt_enabled; ?>:</td><td align="left"><input type="checkbox" name="qm_en" <?php if($config['quiet_mode']['enabled']) echo "checked";?> /></td></tr>
                <tr><td align="right"><?php echo $is_cn ? "时间范围" : "Time Range"; ?>:</td><td align="left">
                    <input type="time" name="qm_start" style="width:100px;" value="<?php echo $config['quiet_mode']['start_time'];?>" /> - 
                    <input type="time" name="qm_end" style="width:100px;" value="<?php echo $config['quiet_mode']['end_time'];?>" />
                </td></tr>

                <tr>
                    <td colspan="2" style="background: #ffffff; text-align: center; padding: 15px;">
                        <input type="submit" name="action" value="save" style="font-weight: bold; width: 140px;" value="<?php echo $txt_save_btn; ?>" />
                        <button type="submit" name="action" value="test" style="background: #b55; color: white; width: 140px; cursor: pointer; border: 1px solid #000;"><?php echo $txt_test_btn; ?></button>
                    </td>
                </tr>
            </tbody>
        </table>
        </form>
    </div>

    <div class="footer">
        Pi-Star / Pi-Star Dashboard, &copy; Andy Taylor (MW0MWZ) 2014-2026.<br />
        Push Notifier Mod by BA4SMQ.
    </div>
</div>
</body>
</html>
