const osc  = require("osc");
const R    = require("ramda");
const net  = require("net");

// create a server to listen for a station
function createServer({ port, onMessage, stationId }){

  net.createServer(function(socket){
    socket.on("data", function(data){
      onMessage({ data, port, stationId });
    });

    socket.on("close", function() {
      console.log(`Controls socket server closed (${port})`);
    });

  })
  .listen(port, () => {
    console.log(`Controls listening for OSC messages on port ${port}`);
  });

}

/**
 * create some servers to listen for message from Python for each control station
 * and also create an outgoing OSC server (when the client clicks a button)
 * @param  {Function} onMessage function to call when a message is generated
 *   by clicking a button
 * @param {String} address
 * @return {Server} an OSC server that can send messages
 */
module.exports = function createControlsServers({ onMessage, address }){

  // start the "listening" servers
  R.range(9000, 9006).forEach((port, i) => {
    return createServer({
      port,
      onMessage,
      stationId: i
    });
  });

  // Create an osc.js UDP Port listening on the specified port.
  // https://www.npmjs.com/package/osc
  const oscServer = new osc.UDPPort({
    localAddress: address,
    localPort: 57121, // not needed, any port
    metadata: true
  });

  oscServer.open();


  // we need a server to send osc messages back to python.
  return oscServer;

};
