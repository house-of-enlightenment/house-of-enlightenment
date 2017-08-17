const gulp = require("gulp");
const quench = require("../quench.js");
const path = require("path");
const spawn = require("child_process").spawn;
const runSequence = require("run-sequence");

const createCopyTask        = require("../tasks/createCopyTask.js");
const createCssTask         = require("../tasks/createCssTask.js");
const createJsTask          = require("../tasks/createJsTask.js");
const createNodemonTask     = require("../tasks/createNodemonTask.js");
const createBrowserSyncTask = require("../tasks/createBrowserSyncTask.js");

const yargs = require("yargs").options({
  "osc-server": {
    default: "127.0.0.1",
    type: "string"
  }
}).argv;


// task to read the layout file and run the controls server with that file
module.exports = function controlsTask(projectRoot) {

  const controlsRoot = path.resolve(projectRoot, "./javascript/controls/");
  const controlsDest = path.resolve(projectRoot, "./javascript/controls/build/");
  const serverDir = path.resolve(controlsRoot, "./server/");


  /**
   * main entry controls task
   * use --watch and --env development/production
   */
  gulp.task("controls-build", function(){


    createCopyTask("controls-copy", {
      src: [
        `${controlsRoot}/client/index.html`
      ],
      dest: controlsDest,
      base: `${controlsRoot}/client/`
    });


    createCssTask("controls-css", {
      src: [
        `${controlsRoot}/client/scss/**/*.scss`,
        `${controlsRoot}/client/js/**/*.scss`
      ],
      dest: `${controlsDest}/css/`,
      watch: [
        `${controlsRoot}/client/scss/**/*.scss`,
        `${controlsRoot}/client/js/**/*.scss`
      ],
      filename: "index.css"
    });


    createJsTask("controls-js", {
      dest: `${controlsDest}/js/`,
      files: [
        {
          gulpTaskId: "controls-js-index",
          entry: `${controlsRoot}/client/js/index.js`,
          filename: "index.js",
          watch: [
            `${controlsRoot}/client/js/**/*.js`,
            `${controlsRoot}/client/js/**/*.jsx`
          ]
        }
      ]
    });


    createNodemonTask("controls-nodemon", {
      script: path.resolve(serverDir, "server.js"),
      watch: [ serverDir ]
    });


    createBrowserSyncTask("controls-browser-sync", {
      files: controlsDest + "/**",
      proxy: "http://localhost:3032"
    });



    const controlsTasks = ["controls-copy", "controls-css", "controls-js"];

    if (quench.isWatching()){
      return runSequence(
        controlsTasks,
        "controls-nodemon",
        "controls-browser-sync"
      );
    }
    else {
      return runSequence(controlsTasks);
    }

  });


  /**
   * run the controls server (after it is already built)
   */
  gulp.task("controls", function(cb){

    // run the node server
    // https://stackoverflow.com/questions/10232192/exec-display-stdout-live
    const server = spawn("node",
      [
        "javascript/controls/server/server.js",
        "--osc-server", yargs["osc-server"]
      ],
      { cwd: `${projectRoot}` }
    );

    server.stdout.pipe(process.stdout);

    server.stderr.pipe(process.stderr);

    server.on("exit", (code) => {
      const codeMsg = (code) ? `with code ${code.toString()}` : "";
      console.log(` Controls server stopped ${codeMsg}`);
    });

    cb();

  });

};
