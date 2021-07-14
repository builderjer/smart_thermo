$(document).ready(function(){
    var socket = io();
    socket.on('test', function(msg) {
        console.log(msg.payload)
        // document.getElementById('test').src=msg.payload;
        $('#test').text(msg.payload);
    });
    // $('test').submit(function(event) {
    //     socket.emit('my event', {data: $('#emit_data').val()});
    //     return false;
    // });
    // $('form#broadcast').submit(function(event) {
    //     socket.emit('my broadcast event', {data: $('#broadcast_data').val()});
    //     return false;
    // });
});
