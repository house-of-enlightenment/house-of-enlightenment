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


// task to read the layout file and run the hoe server with that file
module.exports = function hoeTask(projectRoot) {

  const hoeRoot = path.resolve(projectRoot, "./javascript/hoe/");
  const hoeDest = path.resolve(projectRoot, "./javascript/hoe/build/");
  const serverDir = path.resolve(hoeRoot, "./server/");
  const simulatorServerDir = path.resolve(projectRoot, "./javascript/simulator/server/");
  const controlsServerDir = path.resolve(projectRoot, "./javascript/controls/server/");


  const yargs = require("yargs").options({
    "layout": {
      default: undefined,
      type: "string"
    }
  }).argv;

  const layout = yargs.layout || "layout/hoeLayout.json";

  /**
   * main entry hoe task
   * use --watch and --env development/production
   */
  gulp.task("hoe-build", function(){

    createCopyTask("hoe-copy", {
      src: [
        `${hoeRoot}/client/index.html`,
        `${hoeRoot}/client/models/**`
      ],
      dest: hoeDest,
      base: `${hoeRoot}/client/`
    });


    const cssFiles = [
      `${hoeRoot}/client/scss/**/*.scss`,
      `${hoeRoot}/client/js/**/*.scss`,
      `${projectRoot}/javascript/simulator/client/scss/**/*.scss`,
      `${projectRoot}/javascript/simulator/client/js/**/*.scss`,
      `${projectRoot}/javascript/controls/client/scss/**/*.scss`,
      `${projectRoot}/javascript/controls/client/js/**/*.scss`
    ];

    createCssTask("hoe-css", {
      src: cssFiles,
      dest: `${hoeDest}/css/`,
      watch: cssFiles,
      filename: "index.css"
    });


    createJsTask("hoe-js", {
      dest: `${hoeDest}/js/`,
      files: [
        {
          gulpTaskId: "hoe-js-index",
          entry: `${hoeRoot}/client/js/index.js`,
          filename: "index.js",
          watch: [
            `${hoeRoot}/client/js/**/*.js`,
            `${hoeRoot}/client/js/**/*.jsx`,
            `${projectRoot}/layout/**/*.json`
          ]
        }
      ]
    });


    // start the hoe server
    createNodemonTask("hoe-nodemon", {
      script: path.resolve(serverDir, "server.js"),
      args: ["--layout", layout],
      watch: [ serverDir ]
    });

    // start the simulator server
    createNodemonTask("simulator-nodemon", {
      script: path.resolve(simulatorServerDir, "server.js"),
      args: ["--layout", layout],
      watch: [ simulatorServerDir ]
    });

    // start the controls server
    createNodemonTask("controls-nodemon", {
      script: path.resolve(controlsServerDir, "server.js"),
      watch: [ controlsServerDir ]
    });


    createBrowserSyncTask("hoe-browser-sync", {
      files: hoeDest + "/**",
      proxy: "http://localhost:3034"
    });


    const hoeTasks = ["hoe-copy", "hoe-css", "hoe-js"];

    if (quench.isWatching()){
      return runSequence(
        hoeTasks,
        "hoe-nodemon",
        // "controls-nodemon", TODO get nodemon working for controls and server
        // "simulator-nodemon",
        "hoe-browser-sync"
      );
    }
    else {
      return runSequence(hoeTasks);
    }


  });


  /**
   * run the hoe server (after it is already built)
   */
  gulp.task("hoe", ["simulator", "controls"], function(cb){

    // run the node server
    // https://stackoverflow.com/questions/10232192/exec-display-stdout-live
    const server = spawn("node",
      ["javascript/hoe/server/server.js", "--layout", layout],
      { cwd: `${projectRoot}` }
    );

    server.stdout.pipe(process.stdout);

    server.stderr.pipe(process.stderr);

    server.on("exit", (code) => {
      const codeMsg = (code) ? `with code ${code.toString()}` : "";
      console.log(` Simulator server stopped ${codeMsg}`);
    });

    cb();

  });

};
