const express   = require("express");
const app       = express();
const server    = require("http").createServer(app);
const path      = require("path");
const morgan    = require("morgan"); // express logger
const net       = require("net");
const WebSocket = require("ws");
const fs        = require("fs");

const yargs = require("yargs")
  .options({
    "layout": {
      alias: "l",
      describe: "path to layout file",
      required: true
    }
  })
  .help()
  .argv;


const createWebsocket = require("./createWebsocket.js");

// initialize WebSocket
createWebsocket(server);


const buildDirectory = path.resolve(__dirname, "../build");
const layoutDirectory = path.resolve(__dirname, "../../layout");
const layoutFile = path.resolve(process.cwd(), yargs.layout);

app.use(morgan("dev"));     /* debugging: "default", "short", "tiny", "dev" */
// app.use(express.json());  // for parsing json
// app.use(express.favicon(__dirname + "/public/favicon.ico"));


app.get("/layout.json", function(req, res){
  res.sendFile(layoutFile);
});

// server the layout directory
app.use("/layout", express.static(layoutDirectory));

// forward all traffic to index.html
app.get("/", function(req, res){

  try {
    // check to see if the layout file exists, will throw if not
    fs.accessSync(layoutFile, fs.R_OK);
    res.sendFile(path.resolve(buildDirectory, "index.html"));
  }
  catch (e) {
    res.status(500).send(`<h2>layout file doesn't exits!!</h2> <code>${layoutFile}</code>`);
  }
});

app.use(express.static(buildDirectory));


console.log("LAYOUT", layoutDirectory);

server.listen(3030, () => {
  console.log("Listening on port 3030...");
});



/* socket to websocket! */
// create a socket server to listen to the OPC data
// it's a buffer, forward to the websocket server (port 3030)
net.createServer(function (socket) {

  // connect to the web server
  const ws = new WebSocket("ws://localhost:3030", { });

  ws.on("open", function open() {

    // forward socket messages from python to the browser
    socket.on("data", function (data) {
      ws.send(data);
    });

  });

}).listen(7890);




module.exports = app;
