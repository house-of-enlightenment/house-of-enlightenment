const express   = require("express");
const app       = express();
const server    = require("http").createServer(app);
const path      = require("path");
const morgan    = require("morgan"); // express logger
const fs        = require("fs");
const request   = require("request");


const buildDirectory = path.resolve(__dirname, "../build");
const indexHtml = path.resolve(buildDirectory, "index.html");
const simulatorServer = "http://localhost:3030";
// const controlsServer = "http://localhost:3032";

app.use(morgan("dev"));     /* debugging: "default", "short", "tiny", "dev" */
// app.use(express.json());  // for parsing json
// app.use(express.favicon(__dirname + "/public/favicon.ico"));


// proxy all these request to the simulator server
app.use("/layout*", function(req, res){
  request(simulatorServer + req.originalUrl).pipe(res);
});


// index.html
app.get("/", function(req, res){

  // check if index.html is there
  if (!fileExists(indexHtml)){
    res.status(500).send("<h2>index.html doesn't exist!!</h2> did you run <code>gulp hoe-build</code>?");
    return;
  }

  // send index.html
  res.sendFile(indexHtml);

});


app.use(express.static(buildDirectory));


server.listen(3034, () => {
  // eslint-disable-next-line no-console
  console.log("HOE listening on port 3034...");
});


// catch any crazy errors
process.on("uncaughtException", function(e){
  server.close();
  console.log("hoe server error: ", e);
});

/**
 * fileExists
 * @param  {String} filepath : path to the file
 * @return {Boolean} true if the filepath exists and is readable
 */
function fileExists(filepath) {
  try {
    fs.accessSync(filepath, fs.R_OK);
    return true;
  }
  catch(e) {
    return false;
  }
}

module.exports = app;
