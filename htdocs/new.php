<?php
require '../config/settings.inc.php';
define("IEM_APPID", 1);
include_once('../include/myview.php');

$t = new MyView();
$t->render('homepage.phtml');
?>
