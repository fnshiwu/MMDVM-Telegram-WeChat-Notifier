<?php
// MMDVM Push Notifier Admin Page - Optimized for Pi-Star
$configFile = '/etc/mmdvm_push.json';

// 初始化默认配置
if (!file_exists($configFile)) {
    $defaultConfig = [
        "push_tg_enabled" => false, "push_wx_enabled" => false,
        "my_callsign" => "", "tg_token" => "", "tg_chat_id" => "", "wx_token" => "",
        "ignore_list" => [], "focus_list" => [],
        "quiet_mode" => ["enabled" => false, "start_time" => "23:00", "end_time" => "07:00"]
    ];
    file_put_contents($configFile, json_encode($defaultConfig));
}

$config = json_decode(file_get_contents($configFile), true);
$message = "";

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'];
    
    // 保存逻辑
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
        $message = "设置已成功保存！";
    }

    // 测试推送逻辑
    if ($action === 'test') {
        $test_msg = "🔔 MMDVM 推送测试成功！\n呼号: " . ($_POST['callsign'] ?: "未设置") . "\n时间: " . date("H:i:s");
        if (isset($_POST['tg_en'])) {
            file_get_contents("https://api.telegram.org/bot".trim($_POST['tg_token'])."/sendMessage?chat_id=".trim($_POST['tg_chat_id'])."&text=".urlencode($test_msg));
        }
        if (isset($_POST['wx_en'])) {
            file_get_contents("http://www.pushplus.plus/send?token=".trim($_POST['wx_token'])."&title=推送测试&content=".urlencode($test_msg));
        }
        $message = "测试消息已发出，请检查手机！";
    }
}
?>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" type="text/css" href="css/pistar-css.php">
    <title>Pi-Star - 推送设置</title>
    <style>
        .content { padding: 10px; color: #000; }
        textarea { width: 95%; height: 60px; font-family: monospace; text-transform: uppercase; }
        .btn-red { background-color: #8b0000; color: white; border: none; padding: 8px 15px; cursor: pointer; font-weight: bold; }
        .btn-normal { padding: 8px 15px; cursor: pointer; }
    </style>
</head>
<body>
<div id="container">
    <div id="header">推送功能管理 - BA4SMQ</div>
    <form method="post">
    <div id="main" class="content">
        <?php if($message) echo "<div style='background:#dfd; padding:10px; margin-bottom:10px;'>$message</div>"; ?>
        <table style="width:100%;">
            <tr><th colspan="2">核心配置</th></tr>
            <tr><td align="right" width="30%">我的呼号:</td><td><input type="text" name="callsign" value="<?php echo $config['my_callsign'];?>"></td></tr>
            
            <tr><th colspan="2">Telegram 推送</th></tr>
            <tr><td align="right">启用:</td><td><input type="checkbox" name="tg_en" <?php if($config['push_tg_enabled']) echo "checked";?>></td></tr>
            <tr><td align="right">Token:</td><td><input type="password" name="tg_token" style="width:90%" value="<?php echo $config['tg_token'];?>"></td></tr>
            <tr><td align="right">ChatID:</td><td><input type="text" name="tg_chat_id" value="<?php echo $config['tg_chat_id'];?>"></td></tr>

            <tr><th colspan="2">微信 (PushPlus)</th></tr>
            <tr><td align="right">启用:</td><td><input type="checkbox" name="wx_en" <?php if($config['push_wx_enabled']) echo "checked";?>></td></tr>
            <tr><td align="right">Token:</td><td><input type="password" name="wx_token" style="width:90%" value="<?php echo $config['wx_token'];?>"></td></tr>
