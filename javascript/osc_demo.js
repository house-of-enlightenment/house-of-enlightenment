var osc = require("osc");

// Create an osc.js UDP Port listening on port 57121.
var udpPort = new osc.UDPPort({
  localAddress: "0.0.0.0",
  localPort: 57121,
  metadata: true
});

// Listen for incoming OSC bundles.
udpPort.on("bundle", function (oscBundle, timeTag, info) {
    console.log("An OSC bundle just arrived for time tag", timeTag, ":", oscBundle);
    console.log("Remote info is: ", info);
});

// Open the socket.
udpPort.open();


// When the port is read, send an OSC message to, say, SuperCollider
udpPort.on("ready", function () {
  console.log('READY');
  setInterval(send, 1000);
});


function send() {
  console.log('Sending message');
  udpPort.send({
    address: "/button",
    args: [
      {
        type: "i",
        value: 100
      }
    ]
  }, "127.0.0.1", 7000);
}
