const express   = require("express");
const app       = express();
const server    = require("http").createServer(app);
const path      = require("path");
const morgan    = require("morgan"); // express logger

const createWebsocket = require("./createWebsocket.js");

// initialize WebSocket
createWebsocket(server);


const buildDirectory = path.resolve(__dirname, "../build");

app.use(morgan("dev"));     /* debugging: "default", "short", "tiny", "dev" */
// app.use(express.json());  // for parsing json
// app.use(express.favicon(__dirname + "/public/favicon.ico"));
app.use(express.static(buildDirectory));


// forward all traffic to index.html
app.get("*", function(req, res){
  res.sendFile(path.resolve(buildDirectory, "index.html"));
});

server.listen(3030, () => {
  console.log("Listening on port 3030...");
});

module.exports = app;
