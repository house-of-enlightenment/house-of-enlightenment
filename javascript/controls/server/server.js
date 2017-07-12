const express   = require("express");
const app       = express();
const server    = require("http").createServer(app);
const path      = require("path");
const morgan    = require("morgan"); // express logger



const buildDirectory = path.resolve(__dirname, "../build");
const indexHtml = path.resolve(buildDirectory, "index.html");

app.use(morgan("dev"));     /* debugging: "default", "short", "tiny", "dev" */
// app.use(express.json());  // for parsing json
// app.use(express.favicon(__dirname + "/public/favicon.ico"));


// index.html
app.get("/", function(req, res){

  // send index.html
  res.sendFile(indexHtml);

});


app.use(express.static(buildDirectory));


server.listen(3032, () => {
  // eslint-disable-next-line no-console
  console.log("Listening on port 3032...");
});


module.exports = app;
