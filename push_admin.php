<?php
// MMDVM Push Notifier Admin Page - Optimized for Pi-Star UI
// File path: /var/www/dashboard/admin/push_admin.php

$configFile = '/etc/mmdvm_push.json';

// 加载配置
$config = json_decode(file_get_contents($configFile), true);

// 处理保存逻辑
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (isset($_POST['action']) && $_POST['action'] === 'save') {
        $config['push_tg_enabled'] = isset($_POST['tg_en']);
        $config['push_wx_enabled'] = isset($_POST['wx_en']);
        $config['my_callsign'] = strtoupper(trim($_POST['callsign']));
        $config['tg_token'] = trim($_POST['tg_token']);
        $config['tg_chat_id'] = trim($_POST['tg_chat_id']);
        $config['wx_token'] = trim($_POST['wx_token']);
        
        // 处理列表（逗号或换行分隔转为数组）
        $config['ignore_list'] = array_filter(array_map('trim', explode("\n", strtoupper($_POST['ignore_list']))));
        $config['focus_list'] = array_filter(array_map('trim', explode("\n", strtoupper($_POST['focus_list']))));
        
        // 处理静音模式
        $config['quiet_mode']['enabled'] = isset($_POST['qm_en']);
        $config['quiet_mode']['start_time'] = $_POST['qm_start'];
        $config['quiet_mode']['end_time'] = $_POST['qm_end'];

        file_put_contents($configFile, json_encode($config, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT));
        $message = "设置已成功保存！";
    }
}
?>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link rel="stylesheet" type="text/css" href="css/pistar-css.php" />
    <title>Pi-Star - 推送设置</title>
    <style>
        .setting-box { background-color: #eeeeee; padding: 15px; border-radius: 5px; color: #000; margin-bottom: 10px; }
        .btn-test { background-color: #8b0000; color: white; border: none; padding: 5px 15px; cursor: pointer; }
        textarea { width: 100%; height: 60px; font-family: monospace; }
    </style>
</head>
<body>
<div id="container">
    <div id="header">推送功能管理 - BA4SMQ</div>
    
    <form method="post" action="">
    <div id="main">
        <?php if(isset($message)) echo "<div style='color:green; font-weight:bold; margin-bottom:10px;'>$message</div>"; ?>

        <table style="width:100%; border:none;">
            <tr>
                <th colspan="2">核心配置</th>
            </tr>
            <tr>
                <td align="right" width="30%">我的呼号:</td>
                <td><input type="text" name="callsign" value="<?php echo $config['my_callsign'];?>" placeholder="例如: BA4SMQ" /></td>
            </tr>
            
            <tr><th colspan="2">Telegram 推送设置</th></tr>
            <tr>
                <td align="right">启用 TG 推送:</td>
                <td><input type="checkbox" name="tg_en" <?php if($config['push_tg_enabled']) echo "checked";?> /></td>
            </tr>
            <tr>
                <td align="right">Bot Token:</td>
                <td><input type="password" name="tg_token" style="width:80%" value="<?php echo $config['tg_token'];?>" /></td>
            </tr>
            <tr>
                <td align="right">Chat ID:</td>
                <td><input type="text" name="tg_chat_id" value="<?php echo $config['tg_chat_id'];?>" /></td>
            </tr>

            <tr><th colspan="2">微信 (PushPlus) 设置</th></tr>
            <tr>
                <td align="right">启用微信推送:</td>
                <td><input type="checkbox" name="wx_en" <?php if($config['push_wx_enabled']) echo "checked";?> /></td>
            </tr>
            <tr>
                <td align="right">PushPlus Token:</td>
                <td><input type="password" name="wx_token" style="width:80%" value="<?php echo $config['wx_token'];?>" /></td>
            </tr>

            <tr><th colspan="2">黑白名单管理 (每行一个呼号)</th></tr>
            <tr>
                <td align="right">忽略列表 (Ignore):<br/><small>不推送这些人的通联</small></td>
                <td><textarea name="ignore_list"><?php echo implode("\n", $config['ignore_list']);?></textarea></td>
            </tr>
            <tr>
                <td align="right">关注列表 (Focus):<br/><small>优先或特殊提醒</small></td>
                <td><textarea name="focus_list"><?php echo implode("\n", $config['focus_list']);?></textarea></td>
            </tr>

            <tr><th colspan="2">静音时段 (Quiet Mode)</th></tr>
            <tr>
                <td align="right">启用静音:</td>
                <td><input type="checkbox" name="qm_en" <?php if($config['quiet_mode']['enabled']) echo "checked";?> /></td>
            </tr>
            <tr>
                <td align="right">开始时间:</td>
                <td><input type="time" name="qm_start" value="<?php echo $config['quiet_mode']['start_time'];?>" /> (通常为深夜)</td>
            </tr>
            <tr>
                <td align="right">结束时间:</td>
                <td><input type="time" name="qm_end" value="<?php echo $config['quiet_mode']['end_time'];?>" /> (通常为早晨)</td>
            </tr>

            <tr>
                <td colspan="2" align="center" style="padding:20px;">
                    <button type="submit" name="action" value="save" style="font-weight:bold; padding: 10px 30px;">保存所有设置</button>
                    <button type="button" onclick="testPush()" class="btn-test">发送测试推送</button>
                </td>
            </tr>
        </table>
    </div>
    </form>
    
    <div id="footer">Pi-Star / MMDVM Notifier by BA4SMQ</div>
</div>

<script>
function testPush() {
    alert('正在发送测试请求到后台脚本...\n请检查手机 Telegram 或微信。');
    // 这里可以添加一个简单的 AJAX 调用 push_script.py 的测试接口
}
</script>
</body>
</html>
