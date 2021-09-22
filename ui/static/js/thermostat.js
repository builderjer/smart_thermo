// This script controls the mqtt client and subscribes to several aspects
// of the weather.
// It pulls it's information from DarkSky API

var __author__ = "builderjer"
var __version__ = "0.1.0"

function sensor_temps() {
  console.log('get temps')
  socket.emit('update_temps')
}

function test_me() {
  console.log('testing me');
  socket.emit('add_sensor', {'pin': 4, 't': 'lm35'});
};

function change_state(msg) {
    console.log('state changed to ', msg)
  if (msg === 'OFF') {
    $('#off_indicator').attr('class', 'in_a_bubble clickable light_background');
  }
  else {
      $('#off_indicator').attr('class', 'in_a_bubble clickable dark_background');
  };
  if (msg === 'COOL') {
    $('#cool_indicator').attr('class', 'in_a_bubble clickable light_background');
  }
  else {
    $('#cool_indicator').attr('class', 'in_a_bubble clickable dark_background');
  };
  if (msg === 'HEAT') {
    $('#heat_indicator').attr('class', 'in_a_bubble clickable light_background');
  }
  else {
    $('#heat_indicator').attr('class', 'in_a_bubble clickable dark_background');
  };
  if (msg === 'VENT') {
    $('#vent_indicator').attr('class', 'in_a_bubble clickable light_background');
  }
  else {
    $('#vent_indicator').attr('class', 'in_a_bubble clickable dark_background');
  };
};

function change_desired_temp(msg) {
  temp = Math.round(parseInt(msg));
  pretty_temp = temp.toString() + '\xB0';
  $('#desired_temp').text(pretty_temp);
};

function get_area_temp(msg) {
  console.log(msg)
  temp = Math.round(parseInt(msg))
  pretty_temp = temp.toString() + '\xB0'
  $('#house_temp').text(pretty_temp)
}
$(document).ready(function(){
    console.log(socket)
//
// Weather section
    socket.on('forecast', function(msg) {
        weather = msg.forecastday[0].day;
        console.log(weather)
        // var weather = msg;
        $('#high_temp').text(Math.round(weather.maxtemp_f));
        $('#low_temp').text(Math.round(weather.mintemp_f));
        console.log(weather.condition);
        icon = weather.condition.icon;
        $('#forecast_summary').text(weather.condition.text);
        // icon = "{{ url_for('static', filename='" + weather.condition.icon + "') }}";
        socket.emit('weather_icon', weather.condition.icon)
        console.log(icon);
        // $('#f_icon').attr("src", icon);
    })

    socket.on('f_icon', function(msg) {
        console.log('f_icon', msg)
        $('#forecast_icon').attr('src', msg);
    })

    socket.on('current', function(msg) {
        console.log(msg);
        temp = parseInt(msg.temp_f).toString() + '\xB0';
        $('#outside_temp').text(temp);
        $('#current_summary').text(msg.condition.text);
        socket.emit('current_icon', msg.condition.icon);
    })

    socket.on('c_icon', function(msg) {
        console.log('f_icon', msg)
        $('#current_icon').attr('src', msg);
    })

    socket.on('inside_temperature', function(msg) {
        // console.log(msg);
        temp = Math.round(parseInt(msg)).toString() + '\xB0';
        // console.log(temp)
        $('#house_temp').text(temp);
    });

    socket.on('thermostat_state', function(msg) {
        change_state(msg);
    });

    socket.on('desired_temp', function(msg) {
        change_desired_temp(msg);
    });

    socket.on('sensor_temps', function(msg) {
      console.log(msg);
      $('#house_temp').text(msg + '\xB0');
    });

    socket.on('changed_temp', function(msg) {
      console.log(msg + ' in change_desired_temp');
      change_desired_temp(msg)
      // $('#desired_temp').text(msg) + '&deg';
    });
    socket.on('my_response', function(msg) {
      console.log(msg + ' yes, emiting add_sensor');
    });
    socket.on('thermostat_data', function(msg) {
      console.log(msg)
      change_state(msg.state)
      change_desired_temp(msg.desired_temp)
      // socket.emit('get_area_temp', msg.default_area)

      // get_area_temp(msg.default_area)
      // console.log(msg)
      // var t = JSON.parse(msg)
      // console.log(t)
      // change_state(t.state)
    })
    socket.on('change_thermostat_state', function(msg) {
      console.log(msg);
      change_state(msg);
    });
    socket.on('area_temp', function(msg) {
      get_area_temp(msg)
    })
    $('#off_indicator').click(function() {
      socket.emit('change_state', 'OFF');
    });
    $('#heat_indicator').click(function() {
      socket.emit('change_state', 'HEAT');
    });
    $('#cool_indicator').click(function() {
      socket.emit('change_state', 'COOL');
    });
    $('#vent_indicator').click(function() {
      socket.emit('change_state', 'VENT');
    });

    $('#down_arrow').click(function() {
      var desired_temp = parseInt($('#desired_temp').text());
      socket.emit('change_desired_temp', desired_temp - 1);
    });
    $('#up_arrow').click(function() {
      var desired_temp = parseInt($('#desired_temp').text());
      socket.emit('change_desired_temp', desired_temp + 1);
    });
    $('#room_temp').click(function() {
      console.log('roomtemps');
      socket.emit('add_sensor', 'add me');
    });
});
