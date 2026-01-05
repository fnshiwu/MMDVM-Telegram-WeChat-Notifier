<?php
session_start();
$configFile = '/etc/mmdvm_push.json';
$serviceName = 'mmdvm_push.service';

if (!file_exists($configFile)) {
    shell_exec('sudo rpi-rw');
    $initialConfig = [
        "my_callsign" => "BA4SMQ",
        "min_duration" => 5.0,
        "quiet_mode" => ["enabled" => false, "start" => "23:00", "end" => "07:00"],
        "push_tg_enabled" => false, "tg_token" => "", "tg_chat_id" => "",
        "push_wx_enabled" => false, "wx_token" => "",
        "ignore_list" => [], "focus_list" => [],
        "ui_lang" => "cn"
    ];
    file_put_contents($configFile, json_encode($initialConfig, 192));
    shell_exec('sudo rpi-ro');
}
$config = json_decode(file_get_contents($configFile), true);

if (isset($_GET['set_lang'])) { 
    shell_exec('sudo rpi-rw');
    $_SESSION['pistar_push_lang'] = $_GET['set_lang']; 
    $config['ui_lang'] = $_GET['set_lang'];
    file_put_contents($configFile, json_encode($config, 192));
    shell_exec('sudo rpi-ro');
}
$current_lang = isset($_SESSION['pistar_push_lang']) ? $_SESSION['pistar_push_lang'] : ($config['ui_lang'] ?? 'cn');
$is_cn = ($current_lang === 'cn');

$lang = [
    'cn' => [
        'nav_dash'=>'仪表盘','nav_admin'=>'管理','nav_log'=>'日志','nav_power'=>'电源','nav_push'=>'推送设置',
        'srv_ctrl'=>'服务控制','status'=>'状态','run'=>'运行中','stop'=>'已停止',
        'btn_start'=>'启动','btn_stop'=>'停止','btn_res'=>'重启','btn_test'=>'发送测试','btn_save'=>'保存设置',
        'conf'=>'推送功能设置','my_call'=>'我的呼号','min_dur'=>'最小推送时长 (秒)',
        'qm_en'=>'开启静音时段','qm_range'=>'静音时间范围','tg_set'=>'Telegram 设置','wx_set'=>'微信 (PushPlus) 设置','en'=>'启用推送',
        'ign_list'=>'忽略列表 (黑名单)','foc_list'=>'关注列表 (白名单)'
    ],
    'en' => [
        'nav_dash'=>'Dashboard','nav_admin'=>'Admin','nav_log'=>'Live Logs','nav_power'=>'Power','nav_push'=>'Push Settings',
        'srv_ctrl'=>'Service Control','status'=>'Status','run'=>'RUNNING','stop'=>'STOPPED',
        'btn_start'=>'Start','btn_stop'=>'Stop','btn_res'=>'Restart','btn_test'=>'Send Test','btn_save'=>'SAVE SETTINGS',
        'conf'=>'Push Notifier Settings','my_call'=>'My Callsign','min_dur'=>'Min Duration (sec)',
        'qm_en'=>'Quiet Mode','qm_range'=>'Quiet Time Range','tg_set'=>'Telegram Settings','wx_set'=>'WeChat (PushPlus) Settings','en'=>'Enable',
        'ign_list'=>'Ignore List','foc_list'=>'Focus List'
    ]
][$current_lang];

$alertMsg = "";
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'];
    if ($action === 'save') {
        shell_exec('sudo rpi-rw');
        $config['my_callsign'] = strtoupper(trim($_POST['callsign']));
        $config['min_duration'] = floatval($_POST['min_duration']);
        $config['quiet_mode']['enabled'] = isset($_POST['qm_en']);
        $config['quiet_mode']['start'] = $_POST['qm_start'];
        $config['quiet_mode']['end'] = $_POST['qm_end'];
        $config['push_tg_enabled'] = isset($_POST['tg_en']);
        $config['tg_token'] = trim($_POST['tg_token']);
        $config['tg_chat_id'] = trim($_POST['tg_chat_id']);
        $config['push_wx_enabled'] = isset($_POST['wx_en']);
        $config['wx_token'] = trim($_POST['wx_token']);
        $config['ignore_list'] = array_filter(array_map('trim', explode("\n", strtoupper($_POST['ignore_list']))));
        $config['focus_list'] = array_filter(array_map('trim', explode("\n", strtoupper($_POST['focus_list']))));
        file_put_contents($configFile, json_encode($config, 192));
        shell_exec('sudo rpi-ro');
        $alertMsg = $is_cn ? "设置已保存！" : "Settings Saved!";
    }
    if ($action === 'test') {
        $test_msg = "🚀 MMDVM Push Test\nCall: " . $_POST['callsign'] . "\nTime: " . date("H:i:s");
        if (isset($_POST['tg_en'])) @file_get_contents("https://api.telegram.org/bot".trim($_POST['tg_token'])."/sendMessage?".http_build_query(["chat_id"=>trim($_POST['tg_chat_id']), "text"=>$test_msg]));
        if (isset($_POST['wx_en'])) @file_get_contents("http://www.pushplus.plus/send?".http_build_query(["token"=>trim($_POST['wx_token']), "title"=>"Test", "content"=>$test_msg]));
        $alertMsg = $is_cn ? "测试已发出！" : "Test Sent!";
    }
    if (in_array($action, ['start', 'stop', 'restart'])) { shell_exec("sudo systemctl $action $serviceName"); }
}
$is_running = (strpos(shell_exec("sudo systemctl status $serviceName"), 'active (running)') !== false);
?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link rel="stylesheet" type="text/css" href="css/pistar-css.php" />
    <title>Push Notifier Settings</title>
    <style type="text/css">
        textarea { width: 95%; height: 55px; font-family: monospace; font-size: 12px; }
        input[type="text"], input[type="password"], input[type="number"], input[type="time"] { width: 95%; height: 22px; }
        .time-box { width: 42% !important; display: inline-block; }
        .btn-test { background: #b55; color: white; font-weight: bold; border: 1px solid #000; cursor: pointer; }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <div style="font-size: 8px; text-align: left; padding-left: 8px; float: left;">Hostname: <?php echo exec('hostname'); ?></div>
        <h1>Pi-Star Push Notifier - BA4SMQ</h1>
        <p style="text-align: right; padding-right: 10px; color: #fff;">
            <a href="/" style="color: #fff;"><?php echo $lang['nav_dash']; ?></a> | 
            <a href="/admin/" style="color: #fff;"><?php echo $lang['nav_admin']; ?></a> | 
            <a href="/admin/power.php" style="color: #fff;"><?php echo $lang['nav_power']; ?></a> | 
            <a href="/admin/push_admin.php" style="color: #fff; font-weight: bold;"><?php echo $lang['nav_push']; ?></a> | 
            <a href="?set_lang=<?php echo $is_cn?'en':'cn';?>" style="color: #ffff00;">[<?php echo $is_cn?'English':'中文';?>]</a>
        </p>
    </div>
    <div class="contentwide">
        <?php if($alertMsg) echo "<div style='background:#ffffc0; color:#000; padding:5px; text-align:center; border:1px solid #666;'>$alertMsg</div>"; ?>
        <form method="post">
        <table class="settings">
            <thead><tr><th colspan="2"><?php echo $lang['srv_ctrl']; ?></th></tr></thead>
            <tr><td align="right" width="35%"><?php echo $lang['status']; ?>:</td><td><b style="color:<?php echo $is_running?'#008000':'#ff0000';?>"><?php echo $is_running ? $lang['run'] : $lang['stop']; ?></b></td></tr>
            <tr><td align="right">Action:</td><td>
                <button type="submit" name="action" value="start"><?php echo $lang['btn_start']; ?></button>
                <button type="submit" name="action" value="stop"><?php echo $lang['btn_stop']; ?></button>
                <button type="submit" name="action" value="restart"><?php echo $lang['btn_res']; ?></button>
            </td></tr>
            <thead><tr><th colspan="2"><?php echo $lang['conf']; ?></th></tr></thead>
            <tr><td align="right"><?php echo $lang['my_call']; ?>:</td><td><input type="text" name="callsign" value="<?php echo $config['my_callsign'];?>" /></td></tr>
            <tr><td align="right"><?php echo $lang['min_dur']; ?>:</td><td><input type="number" step="0.1" name="min_duration" value="<?php echo $config['min_duration'];?>" /></td></tr>
            <tr><td align="right"><?php echo $lang['qm_en']; ?>:</td><td><input type="checkbox" name="qm_en" <?php echo ($config['quiet_mode']['enabled']??false)?'checked':'';?> /></td></tr>
            <tr><td align="right"><?php echo $lang['qm_range']; ?>:</td><td>
                <input type="time" name="qm_start" class="time-box" value="<?php echo $config['quiet_mode']['start']??'23:00';?>" /> - 
                <input type="time" name="qm_end" class="time-box" value="<?php echo $config['quiet_mode']['end']??'07:00';?>" />
            </td></tr>
            <thead><tr><th colspan="2"><?php echo $lang['tg_set']; ?></th></tr></thead>
            <tr><td align="right"><?php echo $lang['en']; ?>:</td><td><input type="checkbox" name="tg_en" <?php echo ($config['push_tg_enabled']??false)?'checked':'';?> /></td></tr>
            <tr><td align="right">Token:</td><td><input type="password" name="tg_token" value="<?php echo $config['tg_token'];?>" /></td></tr>
            <tr><td align="right">Chat ID:</td><td><input type="text" name="tg_chat_id" value="<?php echo $config['tg_chat_id'];?>" /></td></tr>
            <thead><tr><th colspan="2"><?php echo $lang['wx_set']; ?></th></tr></thead>
            <tr><td align="right"><?php echo $lang['en']; ?>:</td><td><input type="checkbox" name="wx_en" <?php echo ($config['push_wx_enabled']??false)?'checked':'';?> /></td></tr>
            <tr><td align="right">Token:</td><td><input type="password" name="wx_token" value="<?php echo $config['wx_token'];?>" /></td></tr>
            <thead><tr><th colspan="2"><?php echo $lang['ign_list']; ?></th></tr></thead>
            <tr><td colspan="2" align="center"><textarea name="ignore_list" placeholder="呼号每行一个"><?php echo implode("\n", $config['ignore_list']??[]);?></textarea></td></tr>
            <thead><tr><th colspan="2"><?php echo $lang['foc_list']; ?></th></tr></thead>
            <tr><td colspan="2" align="center"><textarea name="focus_list" placeholder="呼号每行一个"><?php echo implode("\n", $config['focus_list']??[]);?></textarea></td></tr>
            <tr><td colspan="2" align="center" style="padding: 15px;">
                <button type="submit" name="action" value="save" style="width:120px; height:32px; font-weight:bold;"><?php echo $lang['btn_save']; ?></button>
                <button type="submit" name="action" value="test" class="btn-test" style="width:120px; height:32px;"><?php echo $lang['btn_test']; ?></button>
            </td></tr>
        </table></form>
    </div>
    <div class="footer">Pi-Star / Pi-Star Dashboard, Mod by BA4SMQ.</div>
</div>
</body></html>
