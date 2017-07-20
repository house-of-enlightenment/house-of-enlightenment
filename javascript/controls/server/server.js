const express   = require("express");
const app       = express();
const server    = require("http").createServer(app);
const path      = require("path");
const morgan    = require("morgan"); // express logger
const WebSocket = require("ws");
const osc       = require("osc");


const buildDirectory = path.resolve(__dirname, "../build");
const indexHtml = path.resolve(buildDirectory, "index.html");


function forwardWebsocketMsgOverOsc(udpPort) {
  const wss = new WebSocket.Server({ port: 4040 });
  wss.on("connection", function connection(ws) {
    console.log("Websocket connection made");
    ws.on("message", function incoming(message) {
      console.log("Received: %s", message);
      parseAndSend(message, udpPort);
    });
  })
}


function parseAndSend(message, udpPort) {
  var data = JSON.parse(message);

  udpPort.send({
    address: "/button",
    args: [
      {
        type: "i",
        value: data.controlsId
      },
      {
        type: "s",
        value: data.leftOrRight
      }
    ]
  }, "127.0.0.1", 7000);
}


app.use(morgan("dev"));     /* debugging: "default", "short", "tiny", "dev" */
// app.use(express.json());  // for parsing json
// app.use(express.favicon(__dirname + "/public/favicon.ico"));


// index.html
app.get("/", function(req, res){

  // send index.html
  res.sendFile(indexHtml);

});


app.use(express.static(buildDirectory));


// Create an osc.js UDP Port listening on port 57121.
// We never send data back, so this doesn't matter
var udpPort = new osc.UDPPort({
  localAddress: "127.0.0.1",
  localPort: 57121,
  metadata: true
});
udpPort.open();


// When the port is read, send an OSC message to, say, SuperCollider
udpPort.on("ready", function () {
  console.log("READY");
  forwardWebsocketMsgOverOsc(udpPort);

  // TODO: should actually wait for the websocket to be made
  server.listen(3032, () => {
    // eslint-disable-next-line no-console
    console.log("Listening on port 3032...");
  });
})
