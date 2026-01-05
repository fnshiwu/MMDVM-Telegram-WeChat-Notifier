<?php
session_start();
$configFile = '/etc/mmdvm_push.json';
$serviceName = 'mmdvm_push.service';
$scriptPath = '/home/pi-star/MMDVM-Push-Notifier/mmdvm_push.py';

function set_disk($mode) { @shell_exec("sudo rpi-$mode"); }
$config = json_decode(@file_get_contents($configFile), true);

if ($_SERVER['REQUEST_METHOD'] === 'POST' || isset($_GET['set_lang'])) {
    set_disk('rw');
    if (isset($_GET['set_lang'])) { $config['ui_lang'] = $_GET['set_lang']; } 
    elseif ($_POST['action'] === 'save') {
        $config = [
            "my_callsign" => strtoupper(trim($_POST['callsign'])),
            "min_duration" => floatval($_POST['min_duration']),
            "quiet_mode" => ["enabled"=>isset($_POST['qm_en']), "start"=>$_POST['qm_start'], "end"=>$_POST['qm_end']],
            "push_tg_enabled" => isset($_POST['tg_en']), "tg_token" => trim($_POST['tg_token']), "tg_chat_id" => trim($_POST['tg_chat_id']),
            "push_wx_enabled" => isset($_POST['wx_en']), "wx_token" => trim($_POST['wx_token']),
            "ignore_list" => array_filter(array_map('trim', explode("\n", strtoupper($_POST['ignore_list'])))),
            "focus_list" => array_filter(array_map('trim', explode("\n", strtoupper($_POST['focus_list'])))),
            "ui_lang" => $config['ui_lang']
        ];
        file_put_contents($configFile, json_encode($config, 192));
        $alertMsg = ($config['ui_lang'] == 'cn') ? "设置已保存！" : "Settings Saved!";
    }
    
    $action = $_POST['action'];
    if (in_array($action, ['start', 'stop', 'restart'])) shell_exec("sudo systemctl $action $serviceName");
    if ($action === 'test') {
        $out = [];
        exec("/usr/bin/python3 $scriptPath --test 2>&1", $out);
        $alertMsg = "Result: " . implode(" ", $out);
    }
    set_disk('ro');
}

$current_lang = $config['ui_lang'] ?? 'cn';
$is_cn = ($current_lang === 'cn');
$is_running = (strpos(shell_exec("sudo systemctl status $serviceName"), 'active (running)') !== false);
$lang = [
    'cn' => ['nav_dash'=>'仪表盘','nav_admin'=>'管理','nav_push'=>'推送设置','srv_ctrl'=>'服务控制','status'=>'状态','run'=>'运行中','stop'=>'已停止','btn_start'=>'启动','btn_stop'=>'停止','btn_res'=>'重启','btn_test'=>'发送测试','btn_save'=>'保存设置','conf'=>'推送功能设置','my_call'=>'我的呼号','min_dur'=>'最小时长','qm_en'=>'静音时段','tg_set'=>'Telegram 设置','wx_set'=>'微信设置','en'=>'启用'],
    'en' => ['nav_dash'=>'Dashboard','nav_admin'=>'Admin','nav_push'=>'Push Settings','srv_ctrl'=>'Service Control','status'=>'Status','run'=>'RUNNING','stop'=>'STOPPED','btn_start'=>'Start','btn_stop'=>'Stop','btn_res'=>'Restart','btn_test'=>'Send Test','btn_save'=>'SAVE','conf'=>'Settings','my_call'=>'Callsign','min_dur'=>'Min Dur','qm_en'=>'Quiet Mode','tg_set'=>'Telegram','wx_set'=>'WeChat','en'=>'Enable']
][$current_lang];
?>
<!DOCTYPE html><html><head><meta charset="UTF-8"><link rel="stylesheet" type="text/css" href="css/pistar-css.php"><title>Push Settings</title><style>textarea{width:95%;height:60px;}input[type="text"],input[type="password"],input[type="number"]{width:95%;}</style></head>
<body><div class="container"><div class="header"><h1>Pi-Star Push - BA4SMQ</h1><p align="right"><a href="/" style="color:#fff"><?php echo $lang['nav_dash']; ?></a> | <a href="?set_lang=<?php echo $is_cn?'en':'cn';?>" style="color:#ff0">[<?php echo $is_cn?'English':'中文';?>]</a></p></div>
<div class="contentwide">
<?php if(isset($alertMsg)) echo "<div style='background:#ffffc0;padding:5px;text-align:center;'>$alertMsg</div>"; ?>
<form method="post"><table class="settings">
<thead><tr><th colspan="2"><?php echo $lang['srv_ctrl']; ?></th></tr></thead>
<tr><td align="right"><?php echo $lang['status']; ?>:</td><td><b style="color:<?php echo $is_running?'#008000':'#f00';?>"><?php echo $is_running?$lang['run']:$lang['stop'];?></b></td></tr>
<tr><td align="right">Action:</td><td><button type="submit" name="action" value="start"><?php echo $lang['btn_start'];?></button><button type="submit" name="action" value="restart"><?php echo $lang['btn_res'];?></button><button type="submit" name="action" value="stop"><?php echo $lang['btn_stop'];?></button></td></tr>
<thead><tr><th colspan="2"><?php echo $lang['conf']; ?></th></tr></thead>
<tr><td align="right"><?php echo $lang['my_call'];?>:</td><td><input type="text" name="callsign" value="<?php echo $config['my_callsign'];?>"></td></tr>
<tr><td align="right"><?php echo $lang['min_dur'];?>:</td><td><input type="number" step="0.1" name="min_duration" value="<?php echo $config['min_duration'];?>"></td></tr>
<thead><tr><th colspan="2"><?php echo $lang['tg_set'];?></th></tr></thead>
<tr><td align="right"><?php echo $lang['en'];?>:</td><td><input type="checkbox" name="tg_en" <?php echo ($config['push_tg_enabled']??false)?'checked':'';?>> Token: <input type="password" name="tg_token" style="width:150px" value="<?php echo $config['tg_token'];?>"></td></tr>
<thead><tr><th colspan="2"><?php echo $lang['wx_set'];?></th></tr></thead>
<tr><td align="right"><?php echo $lang['en'];?>:</td><td><input type="checkbox" name="wx_en" <?php echo ($config['push_wx_enabled']??false)?'checked':'';?>> Token: <input type="password" name="wx_token" value="<?php echo $config['wx_token'];?>"></td></tr>
<tr><td colspan="2" align="center"><button type="submit" name="action" value="save" style="width:120px"><?php echo $lang['btn_save'];?></button> <button type="submit" name="action" value="test" style="width:120px;background:#b55;color:white;"><?php echo $lang['btn_test'];?></button></td></tr>
</table></form></div></div></body></html>
