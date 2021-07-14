var __author__ = "builderjer"
var __version__ = "0.0.1"

// var current_weather_timer = setInterval(function() {current_weather_display()}, 15 * 60000);
var icons = '';

// function current_weather_display() {
// 	console.log('in weather.js')
// };

socket.on('forecast_high_temperature', function(msg) {
	console.log('high temp', msg)
	$('#high_temp').text(msg);
});

socket.on('forecast_low_temperature', function(msg) {
	$('#low_temp').text(msg);
});

socket.on('forecast_summary', function(msg) {
	$('#daily_summary').text(msg);
});

socket.on('current_outside_temperature', function(msg) {
	$('#outside_temp').text(msg);
});

socket.on('current_weather_icon', function(msg) {
	$('#current_icon').attr('src', msg);
});
