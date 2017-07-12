const gulp = require("gulp");
const spawn = require("child_process").spawn;
const R = require("ramda");
const path = require("path");
const quench = require("../quench.js");

// task to read the layout file and run the simulator server with that file
module.exports = function simulatorTask(config, env) {

  const simulatorRoot = path.resolve(config.root, "./javascript/simulator/");
  const simulatorDest = path.resolve(config.root, "./javascript/simulator/build/");
  const projectRoot = config.root;

  const simulatorTasks = ["copy", "js", "css"];

  const simulatorConfig = {
    "css": {
      watch: [
        `${simulatorRoot}/client/scss/**/*.scss`,
        `${simulatorRoot}/client/js/**/*.scss`
      ],
      stylesheets: [
        {
          gulpTaskId: "css-simulator",
          src: [
            `${simulatorRoot}/client/scss/**/*.scss`,
            `${simulatorRoot}/client/js/**/*.scss`
          ],
          dest: `${simulatorDest}/css/`,
          filename: "index.css"
        }
      ]
    },
    "js": {
      dest: `${simulatorDest}/js/`,
      files: [
        {
          gulpTaskId: "js-index",
          entry: `${simulatorRoot}/client/js/index.js`,
          filename: "index.js",
          watch: [
            `${simulatorRoot}/client/js/**/*.js`,
            `${simulatorRoot}/client/js/**/*.jsx`,
            `${projectRoot}/layout/**/*.json`
          ]
        },
        {
          gulpTaskId: "js-layout",
          entry: `${projectRoot}/javascript/layout-generator/test.js`,
          filename: "layout.js",
          watch: [
            `${projectRoot}/javascript/layout-generator/**/*.js`
          ]
        }
      ]
    },
    "copy": {
      base: `${simulatorRoot}/client/`,
      tasks: [
        {
          gulpTaskId: "copy-simulator",
          src: [
            `${simulatorRoot}/client/index.html`,
            `${simulatorRoot}/client/layout.html`,
            `${simulatorRoot}/client/models/**`,
            `${simulatorRoot}/client/layout/**` // need csv
          ],
          dest: simulatorDest
        }
      ]
    }
  };


  // HACK to make gulp happy
  gulp.task("simulator", function(cb){ cb(); });

  /**
   * run the simulator server
   */
  gulp.task("simulator:server", function(cb){

    const layout = R.path(["yargs", "layout"], config) || "layout/hoeLayout.json";

    // run the node server
    // https://stackoverflow.com/questions/10232192/exec-display-stdout-live
    const server = spawn("node",
      ["javascript/simulator/server/server.js", "--layout", layout],
      { cwd: `${projectRoot}` }
    );

    server.stdout.pipe(process.stdout);

    server.stderr.pipe(process.stderr);

    server.on("exit", (code) => {
      console.log("server stopped with code " + code.toString());
    });

  });

  /**
   * simulator server with watcher (to develop)
   */
  gulp.task("simulator:watch", function(next){

    const yargs = require("yargs").options({
      "layout": {
        default: undefined,
        type: "string"
      }
    }).argv;

    const serverDir = path.resolve(simulatorRoot, "./server/");
    const layout = yargs.layout || path.resolve(projectRoot, "./layout/hoeLayout.json");


    const buildConfig = R.mergeAll([
      {
        env   : "development",
        watch : true,
        tasks: [simulatorTasks, "nodemon", "browserSync"],
        browserSync: {
          root: simulatorDest,
          proxy: "http://localhost:3030"
        },
        nodemon: {
          script: path.resolve(serverDir, "server.js"),
          args: ["--layout", layout],
          watch: [ serverDir ]
        }
      },
      simulatorConfig
    ]);

    quench.build(buildConfig, next);

  });

  /**
   * build for production
   */
  gulp.task("simulator:prod", function(next){

    const simulatorConfig = R.merge(config, {
      env   : "production",
      watch : false,
      tasks: simulatorTasks
    });

    quench.build(simulatorConfig, next);

  });


  /**
   * build for development without a watcher
   */
  gulp.task("simulator:build", function(next){

    const simulatorConfig = R.merge(config, {
      env   : "development",
      watch : false,
      tasks: simulatorTasks
    });

    quench.build(simulatorConfig, next);

  });

};
