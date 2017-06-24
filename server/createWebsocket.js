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
          client.send(JSON.stringify(byteArray));
        }
      });

    });

  });

  return wss;
};
