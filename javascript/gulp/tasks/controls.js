const gulp = require("gulp");
const spawn = require("child_process").spawn;
const R = require("ramda");
const path = require("path");
const quench = require("../quench.js");

// task to read the layout file and run the controls server with that file
module.exports = function controlsTask(config, env) {

  const controlsRoot = path.resolve(config.root, "./javascript/controls/");
  const controlsDest = path.resolve(config.root, "./javascript/controls/build/");
  const projectRoot = config.root;

  const controlsTasks = ["copy", "js", "css"];

  const controlsConfig = {
    "css": {
      watch: [
        `${controlsRoot}/client/scss/**/*.scss`,
        `${controlsRoot}/client/js/**/*.scss`
      ],
      stylesheets: [
        {
          gulpTaskId: "css-controls",
          src: [
            `${controlsRoot}/client/scss/**/*.scss`,
            `${controlsRoot}/client/js/**/*.scss`
          ],
          dest: `${controlsDest}/css/`,
          filename: "index.css"
        }
      ]
    },
    "js": {
      dest: `${controlsDest}/js/`,
      files: [
        {
          gulpTaskId: "js-index",
          entry: `${controlsRoot}/client/js/index.js`,
          filename: "index.js",
          watch: [
            `${controlsRoot}/client/js/**/*.js`,
            `${controlsRoot}/client/js/**/*.jsx`,
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
      base: `${controlsRoot}/client/`,
      tasks: [
        {
          gulpTaskId: "copy-controls",
          src: [
            `${controlsRoot}/client/index.html`,
            `${controlsRoot}/client/layout.html`,
            `${controlsRoot}/client/models/**`,
            `${controlsRoot}/client/layout/**` // need csv
          ],
          dest: controlsDest
        }
      ]
    }
  };


  // HACK to make gulp happy
  gulp.task("controls", function(cb){ cb(); });

  /**
   * run the controls server
   */
  gulp.task("controls:server", function(cb){

    const layout = R.path(["yargs", "layout"], config) || "layout/hoeLayout.json";

    // run the node server
    // https://stackoverflow.com/questions/10232192/exec-display-stdout-live
    const server = spawn("node",
      ["javascript/controls/server/server.js", "--layout", layout],
      { cwd: `${projectRoot}` }
    );

    server.stdout.pipe(process.stdout);

    server.stderr.pipe(process.stderr);

    server.on("exit", (code) => {
      console.log("server stopped with code " + code.toString());
    });

  });

  /**
   * controls server with watcher (to develop)
   */
  gulp.task("controls:watch", function(next){

    const serverDir = path.resolve(controlsRoot, "./server/");

    const buildConfig = R.mergeAll([
      {
        env   : "development",
        watch : true,
        tasks: [controlsTasks, "nodemon", "browserSync"],
        browserSync: {
          root: controlsDest,
          proxy: "http://localhost:3032"
        },
        nodemon: {
          script: path.resolve(serverDir, "server.js"),
          watch: [ serverDir ]
        }
      },
      controlsConfig
    ]);

    quench.build(buildConfig, next);

  });

  /**
   * build for production
   */
  gulp.task("controls:prod", function(next){

    const buildConfig = R.mergeAll([
      {
        env   : "production",
        watch : false,
        tasks: controlsTasks
      },
      controlsConfig
    ]);

    quench.build(buildConfig, next);

  });


  /**
   * build for development without a watcher
   */
  gulp.task("controls:build", function(next){

    const buildConfig = R.mergeAll([
      {
        env   : "development",
        watch : false,
        tasks: controlsTasks
      },
      controlsConfig
    ]);

    quench.build(buildConfig, next);

  });

};
