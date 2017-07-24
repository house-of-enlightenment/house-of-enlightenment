const express   = require("express");
const app       = express();
const server    = require("http").createServer(app);
const path      = require("path");
const morgan    = require("morgan"); // express logger
const WebSocket = require("ws");
const osc       = require("osc");
const fs        = require("fs");

const buildDirectory = path.resolve(__dirname, "../build");
const indexHtml = path.resolve(buildDirectory, "index.html");




function forwardWebsocketMsgOverOsc(udpPort) {

  // websocket for the client to connect o
  const wss = new WebSocket.Server({ port: 4040 });

  wss.on("connection", function connection(ws) {

    console.log("Websocket connection made on 4040");

    ws.on("message", function incoming(message) {
      console.log("Controls message: %s", message);
      parseAndSend(message, udpPort);
    });
  });
}


function parseAndSend(message, udpPort) {
  var data = JSON.parse(message);
  var address = '/input'
  var args = [
    {
      type: "i",
      value: data.stationId
    },
    {
      type: "s",
      value: data.type
    },
    {
      type: "i",
      value: data.id
    },
    {
      type: "s",
      value: data.value || null
    }
  ]

  console.log("Sending OSC: ", address, args)

  // a python script should be listening on port 7000
  udpPort.send({
    address: address,
    args: args,
  }, "127.0.0.1", 7000);
}


app.use(morgan("dev"));     /* debugging: "default", "short", "tiny", "dev" */


// index.html
app.get("/", function(req, res){

  // check if index.html is there
  if (!fileExists(indexHtml)){
    res.status(500).send("<h2>index.html doesn't exist!!</h2> did you run <code>gulp controls-build</code>?");
    return;
  }

  // send index.html
  res.sendFile(indexHtml);

});


app.use(express.static(buildDirectory));


// Create an osc.js UDP Port listening on port 57121.
// We never send data back, so this doesn't matter
// https://www.npmjs.com/package/osc
var udpPort = new osc.UDPPort({
  localAddress: "127.0.0.1",
  localPort: 57121, // default
  metadata: true
});
udpPort.open();


// When the port is read, send an OSC message to, say, SuperCollider
udpPort.on("ready", function () {

  forwardWebsocketMsgOverOsc(udpPort);

  // TODO: should actually wait for the websocket to be made
  server.listen(3032, () => {
    // eslint-disable-next-line no-console
    console.log("Controls listening on port 3032...");
  });
});

udpPort.on("error", function (error) {
    console.log("udpPort error occurred: ", error.message);
});

// when there is an error, properly close all servers
process.on("uncaughtException", function(e){
  console.log("controls server error: ", e);
});

/**
 * fileExists
 * @param  {String} filepath : path to the file
 * @return {Boolean} true if the filepath exists and is readable
 */
const fileExists = module.exports.fileExists = function fileExists(filepath) {
  try {
    fs.accessSync(filepath, fs.R_OK);
    return true;
  }
  catch(e) {
    return false;
  }
};
