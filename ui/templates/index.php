<?php
include_once (__DIR__.'/../../includes/functions.php');

ziggy_session_start();

// Session Variables
if (isset($_SESSION["loggedin"])) {
    $user = $_SESSION["username"];
    $loggedin = true;
}
else {
    $loggedin = false;
}

// Other variables
$version = "0.0.2";
$motd = "Love yourself often";

// Weather Underground  (www.wunderground.com)
$wu_logo = "../assets/img/wu_logo.png";
?>

<html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <title>ZIGGY</title>
        <link href="../assets/css/fontawesome-all.css" rel="stylesheet"/>
        <link href="../assets/css/custom.css" rel="stylesheet"/>
        <link href="../assets/img/favicon.gif" rel="shortcut icon" type="image/gif">

        <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.1.1/jquery.min.js"></script>
        <script src="../assets/js/custom.js"></script>
    </head>
     <body onload="startTime()"> <!--onload="weatherDisplay()"> -->
        <header>
            <div id="head-wrapper">
                <div id="title">ZIGGY</div>
                <div id="time-wrapper">
                    <div id="date" class="time"></div>
                    <div id="clock" class="time"></div>
                </div>
                <div id="weather-wrapper">
                <!--TODO:  Make this direct to the weather Underground website-->
                    <!--<a href="#" onClick="window.location = 'https://www.wunderground.com/weather/us/co/hotchkiss/KCOROGER2'"></a>-->
                    <div id="temp" class="weather">
                        <i class="fab fa-linux"></i>
                    </div>
                    <div id="icon" class="weather">
                        <img id="w_icon"></img>
                    </div>
                </div>
            </div>
            <div id="login">
                <a href="#" onClick="window.location = '<?php if ($loggedin) {echo "/phpSecureLogin/includes/logout.php"; } else {echo "/phpSecureLogin/index.php";}?>'" class="btn btn-wide"><?php if ($loggedin) { echo "LOGOUT"; } else { echo "LOGIN"; }?></a>
            </div>
        </header>
        <div id='main'>
            <article>
                <h2>Hello, my name is Ziggy. <?php echo $loggedin?></h2>
                <h2><?php if ($loggedin) {
                    echo "Logged in as $user"; }?></h2>
                <p><?php include('../assets/text/info.txt'); ?></p>
<!--                <p>I am an experiment in home automation and smarthome technology.</p>-->
                <p>Login to experience everything that I have to offer</p></br>
<!--                <p>Don't have login information? Click<span><a id="register" href="/login/request_account.php"> here </a></span>to register</p>-->
            </article>
            <nav>
                <div id="about" class="btn btn-nav">
                    <a href="/owncloud"><img src="/owncloud/core/img/favicon.png"></img> OwnCloud</a>
                </div>
                <div id="register" class="btn btn-nav">
                    <a href="#"><i class="fa fa-users fa-3x"></i> Register</a>
                </div>
                <div id="contact" class="btn btn-nav">
                    <a href="#"><i class="fa fa-envelope fa-3x"></i> Contact Me</a>
                </div>
            </nav>
            <aside>
                <div id="instructables" class="btn btn-aside">
                    <a href="#"><img src="/assets/img/instructables-logo.png" height="56px"></img>My Instructables</a>
                </div>
                <div id="facebook" class="btn btn-aside">
                <a href="#"><i class="fa fa-facebook-square fa-3x"></i>My Facebook</a>
                </div>
            </aside>
        </div>
        <footer>Version: <?php echo $version?>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <?php echo $motd?></footer>
<!--        <img src="/reneya/?action=stream" width="640" height="480"/>-->
    </body>
</html>
