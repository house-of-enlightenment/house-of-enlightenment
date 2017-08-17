const WebSocket = require("ws");

module.exports = function createWebsocket(onClientMessage){

  // websocket for the client to connect to
  const wss = new WebSocket.Server({ port: 4040 });

  // shortcut function to broadcast to all clients
  // https://github.com/websockets/ws#broadcast-example
  wss.broadcast = function broadcast(data) {
    wss.clients.forEach(function each(client) {
      if (client.readyState === WebSocket.OPEN) {
        client.send(data);
      }
    });
  };


  wss.on("connection", function connection(ws) {

    console.log("Websocket connection made on 4040");

    // when a message arrives (button clicked, etc), alert the caller
    ws.on("message", function incoming(message) {

      // console.log(`Controls message: ${message}`);
      onClientMessage(message);
    });
  });

  return wss;
};
