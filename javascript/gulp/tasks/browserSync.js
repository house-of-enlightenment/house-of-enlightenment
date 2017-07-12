const gulp        = require("gulp");
const quench      = require("../quench.js");
const R           = require("ramda");
const browserSync = require("browser-sync").create();


module.exports = function(config, env){


  if (config.watch !== true){
    quench.logYellow("WARNING", "Trying to run server without watching!  Server not started.");
    return;
  }


  // browserSync settings
  var settings = R.merge({
    port: config.local.browserSyncPort || 3000,
    open: false, // false or  "external"
    notify: false,
    ghostMode: false,

    serverRoot: config.browserSync.root,
    // proxy: 

    // watch these files and reload the browser when they change
    files: [
      config.browserSync.root + "/**",
      // prevent browser sync from reloading twice when the regular file (eg. index.js)
      // and the map file (eg. index.js.map) are generated
      "!**/*.map"
    ]
  }, config.browserSync);



  // if proxy wasn't specified, use the server root
  // use proxy if you have a server running the site already (eg, node server)
  // http://www.browsersync.io/docs/options/#option-proxy
  if (!settings.proxy) {
    // http://www.browsersync.io/docs/options/#option-server
    settings.server = settings.serverRoot;
  }


  /* start browser sync if we have the "watch" option */
  gulp.task("browserSync", function(){

    quench.logYellow("watching", "browser-sync:", JSON.stringify(settings.files, null, 2));
    browserSync.init(settings);

  });


};
