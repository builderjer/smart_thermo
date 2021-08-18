var __author__ = "builderjer"
var __version__ = "0.1.0"

$(document).ready(function() {
    socket.on('current_forecast', function(msg) {
        forecast = JSON.parse(msg);
    });

    socket.on('current_weather', function(msg) {
        current = JSON.parse(msg);
        current_temp = Math.round(parseInt(current.temp_f)).toString() + '\xB0';
        current_summary = current.condition.text;
        current_icon = current.condition.icon;
    });
})
