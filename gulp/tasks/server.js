const gulp        = require("gulp");
const quench      = require("../quench.js");
const path        = require("path");
const browserSync = require("browser-sync").create();
const nodemon     = require("nodemon");

module.exports = function(config, env){


  if (config.watch !== true){
    quench.logYellow("WARNING", "Trying to run server without watching!  Server not started.");
    return;
  }

  // if not using proxy, use this as the server root
  var serverRoot = path.resolve(config.dest);

  // browserSync settings
  var settings = {
    port: config.local.browserSyncPort || 3000,
    open: false, // false or  "external"
    notify: false,
    ghostMode: false,

    // watch these files and reload the browser when they change
    files: [
      config.dest + "/**",
      // prevent browser sync from reloading twice when the regular file (eg. index.js)
      // and the map file (eg. index.js.map) are generated
      "!**/*.map"
    ]
  };


  // the node server
  const hostname = "http://localhost:3030";

  // set the server root, or proxy if it's set in local.js
  // use proxy if you have a server running the site already (eg, IIS)
  if (hostname) {
    // http://www.browsersync.io/docs/options/#option-proxy
    settings.proxy = hostname;
  }
  else {
    // http://www.browsersync.io/docs/options/#option-server
    settings.server = serverRoot;
  }


  /* start browser sync if we have the "watch" option */
  gulp.task("server", ["nodemon"], function(){

    quench.logYellow("watching", "browser-sync:", JSON.stringify(settings.files, null, 2));
    browserSync.init(settings);

  });

  gulp.task("nodemon", function (cb) {

    var started = false;

    const serverDir = path.resolve(__dirname, "../../server/");

    return nodemon({
      script: path.resolve(serverDir, "server.js"),
      args: ["--layout", path.resolve(config.root, "./layout/layout.json")],
      watch: [ serverDir ]
    }).on("start", function () {
      // to avoid nodemon being started multiple times
      // thanks @matthisk
      if (!started) {
        cb();
        started = true;
      }
    })
    .on("restart", function () {
      console.log("restarted!");
    })
    .on("crash", function() {
      console.error("server.js crashed!\n");
      // stream.emit("restart", 10)  // restart the server in 10 seconds
    });
  });
};
