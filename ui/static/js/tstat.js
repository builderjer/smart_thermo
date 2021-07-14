// function tstat_options() {
//   if ('{{ temp }}') {
//     console.log('{{ temp }}')
//   }
//   console.log('tstat_options')
// }
// function wow() {
//   console.log('wow')
// }
// var t = new XMLHttpRequest();
// t.onreadystatechange = function() {
//   if (this.readyState == 4 && this.status == 200) {
//     console.log('here i am');
//     document.getElementById('temp').innerHTML = this.responseText;
//   }
// };
// t.open('GET', 'thermostat', true);
// t.send();

// function test_function() {
//   if ('{{ data }}') {
//     console.log('{{ data }}')
//     document.getElementById('temp').innerHTML = '{{ data }}'
//   }
// }

$(document).ready(function() {
    console.log('jquery ready')
    var socket = io();
    socket.on('test', function(msg) {
        $('#log').append('<p>Received: ' + msg.data + '</p>');
    });
    $('#test').submit(function (event) {
      console.log(event)
        socket.emit('my event', {data: 'hello'})
    })
    $('form#emit').submit(function(event) {
        socket.emit('my event', {data: $('#emit_data').val()});
        return false;
    });
    $('form#broadcast').submit(function(event) {
        socket.emit('my broadcast event', {data: $('#broadcast_data').val()});
        return false;
    });
});
