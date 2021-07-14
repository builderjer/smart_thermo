
var __author__ = "builderjer"
var __version__ = "0.1.0"

$(document).ready(function() {
  socket.on('main_page_js', function(data) {
    console.log(data);
  });
});
