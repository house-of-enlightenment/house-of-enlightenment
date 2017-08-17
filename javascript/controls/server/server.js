const express   = require("express");
const app       = express();
const server    = require("http").createServer(app);
const path      = require("path");
const morgan    = require("morgan"); // express logger
const fs        = require("fs");

const createControlsServers = require("./createControlsServers.js");
const createWebsocket = require("./createWebsocket.js");
const parseClientMessage = require("./parseClientMessage.js");
const parseMessage = require("./parseMessage.js");

const buildDirectory = path.resolve(__dirname, "../build");
const indexHtml = path.resolve(buildDirectory, "index.html");



const yargs = require("yargs")
  .options({
    "osc-server": {
      alias: "o",
      describe: "ip of the server to send OSC data to",
      required: false,
      default: "127.0.0.1"
    }
  })
  .help()
  .argv;


/*

  Python >>OSC>> oscServer >>JSON>> Websocket

  Websocket >>JSON>> oscServer >>OSC>> Python

 */

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

const oscServer = createControlsServers({
  onMessage,
  address: yargs["osc-server"],
  port: 7000
});

const wss = createWebsocket(onClientMessage);



// when we get a message from the python script,
// forward it to the websocket client
function onMessage({ data, stationId }){

  const jsonMessage = parseMessage({ data, stationId });

  console.log("received message from python:", jsonMessage);

  wss.broadcast(jsonMessage);
}


// when we receive a message from the websocket client (button click, etc)
// forward it to the python script via the oscServer
function onClientMessage(jsonMessage){

  const oscMessage = parseClientMessage(jsonMessage);

  console.log(`Sending OSC ${yargs["osc-server"]}:7000:`, JSON.stringify(oscMessage));

  // send osc messages to the python script (listening on port 7000)
  // yargs["osc-server"] will be 127.0.0.1 locally,
  // or something else if python is running on another machine
  oscServer.send(oscMessage, yargs["osc-server"], 7000);

}



// TODO: should actually wait for the websocket to be made
server.listen(3032, () => {
  // eslint-disable-next-line no-console
  console.log("Controls listening on port 3032...");
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
