
// My custom javascript file.  Hope I can get this to work!!

// Author:  Jeremy Brodie
// Email:  builderjer@gmail.com
// Version:  0.0.1

// // New test for running python process
// const { spawn } = require("child_process");

// Establish some variables

var clockTimer = setInterval(function(){ clockDisplay() }, 1000);

function clockDisplay() {
  var dt = new Date();
	var sc = dt.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
	var sd = dt.toLocaleDateString();
	var lc = dt.toLocaleTimeString();
	var ld = dt.toLocaleDateString([], {weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'});

	try {
    	document.getElementById("short_clock").innerHTML = sc;
	}
	catch(TypeError) {
    try {
      document.getElementById("long_clock").innerHTML = lc;
    }

    catch(TypeError) {
      }
	}

	try {
		document.getElementById("short_date").innerHTML = sd;
	}
	catch(TypeError) {
    try {
      document.getElementById("long_date").innerHTML = ld;
    }

    catch(TypeError) {
      }
	}
}
