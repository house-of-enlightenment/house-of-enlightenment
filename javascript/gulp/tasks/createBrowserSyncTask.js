const gulp        = require("gulp");
const quench      = require("../quench.js");
const R           = require("ramda");
const browserSync = require("browser-sync").create();


module.exports = function(taskName, userConfig){

  const defaults = {
    port: 3000,
    open: false, // false or  "external"
    notify: false,
    ghostMode: false

    // server:
    // proxy:
  };

  // prevent browser sync from reloading twice when the regular file (eg. index.js)
  // and the map file (eg. index.js.map) are generated
  const defaultFiles = ["!**/*.map"];


  // watch these files and reload the browser when they change
  // merge the userConfig files
  const files = R.cond([
    // if userConfig.files is an array, concat defaultFiles on it
    [fs => Array.isArray(fs)      , fs => R.concat(fs), defaultFiles],
    // if userConfig.files is a string, append it to the defaultFiles
    [fs => typeof(fs) === "string", fs => R.append(fs, defaultFiles)],
    // if server is defined, watch that directory
    [fs => userConfig.server      , fs => [`${userConfig.server}/**`]],
    // otherwise, return an empty array
    [R.T                          , fs => []]
  ])(userConfig.files);



  // browserSync settings
  var settings = R.mergeAll([defaults, userConfig, { files }]);


  /* start browser sync if we have the "watch" option */
  gulp.task(taskName, function(){

    quench.logYellow("watching", taskName, JSON.stringify(settings.files, null, 2));
    browserSync.init(settings);

  });


};
