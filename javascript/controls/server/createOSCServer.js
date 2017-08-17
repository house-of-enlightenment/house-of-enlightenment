const osc = require("osc");

module.exports = function createOSCServer(onOscMessage){

  // Create an osc.js UDP Port listening on port 57121.
  // https://www.npmjs.com/package/osc
  const oscServer = new osc.UDPPort({
    localAddress: "127.0.0.1",
    localPort: 57121, // default
    metadata: true
  });

  console.log("Controls listening for OSC messaages on port 57121");


  oscServer.open();


  oscServer.on("ready", function () {

  });

  // Listen for incoming OSC bundles.
  // oscServer.on("bundle", handleMessage);

  // Listen for incoming OSC bundles.
  oscServer.on("message", handleMessage);

  oscServer.on("error", function (error) {
    console.log("oscServer error occurred: ", error.message);
  });


  function handleMessage(oscMessage, timeTag, info){
    onOscMessage(oscMessage);
  }

  return oscServer;

};
