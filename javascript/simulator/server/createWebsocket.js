const WebSocket = require("ws");

module.exports = function createWebsocket(server){

  const wss = new WebSocket.Server({ server });

  wss.on("connection", function connection(ws) {

    ws.on("message", function incoming(buffer){

      // OPC byte array
      const byteArray = Array.from(buffer.values());

      // broadcast to all clients
      wss.clients.forEach(function each(client) {
        if (client !== ws && client.readyState === WebSocket.OPEN) {

          const json = JSON.stringify(byteArray);

          // https://github.com/websockets/ws#error-handling-best-practices
          client.send(json, function ack(error){

            if (error){
              console.log("web socket error: ", error);
            }

          });
        }
      });

    });

  });

  wss.on("error", function(error){
    console.log("websocket server error: ", error);
  });

  return wss;
};
