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


// task to read the layout file and run the admin server with that file
module.exports = function adminTask(projectRoot) {

  const adminRoot = path.resolve(projectRoot, "./javascript/admin/");
  const adminDest = path.resolve(projectRoot, "./javascript/admin/build/");
  const serverDir = path.resolve(adminRoot, "./server/");


  /**
   * main entry admin task
   * use --watch and --env development/production
   */
  gulp.task("admin-build", function(){


    createCopyTask("admin-copy", {
      src: [
        `${adminRoot}/client/index.html`
      ],
      dest: adminDest,
      base: `${adminRoot}/client/`
    });


    createCssTask("admin-css", {
      src: [
        `${adminRoot}/client/scss/**/*.scss`,
        `${adminRoot}/client/js/**/*.scss`
      ],
      dest: `${adminDest}/css/`,
      watch: [
        `${adminRoot}/client/scss/**/*.scss`,
        `${adminRoot}/client/js/**/*.scss`
      ],
      filename: "index.css"
    });


    createJsTask("admin-js", {
      dest: `${adminDest}/js/`,
      files: [
        {
          gulpTaskId: "admin-js-index",
          entry: `${adminRoot}/client/js/index.js`,
          filename: "index.js",
          watch: [
            `${adminRoot}/client/js/**/*.js`,
            `${adminRoot}/client/js/**/*.jsx`
          ]
        }
      ]
    });


    createNodemonTask("admin-nodemon", {
      script: path.resolve(serverDir, "server.js"),
      watch: [ serverDir ]
    });


    createBrowserSyncTask("admin-browser-sync", {
      files: adminDest + "/**",
      proxy: "http://localhost:3032"
    });



    const adminTasks = ["admin-copy", "admin-css", "admin-js"];

    if (quench.isWatching()){
      return runSequence(
        adminTasks,
        "admin-nodemon",
        "admin-browser-sync"
      );
    }
    else {
      return runSequence(adminTasks);
    }

  });


  /**
   * run the admin server (after it is already built)
   */
  gulp.task("admin", function(cb){

    // run the node server
    // https://stackoverflow.com/questions/10232192/exec-display-stdout-live
    const server = spawn("node",
      ["javascript/admin/server/server.js"],
      { cwd: `${projectRoot}` }
    );

    server.stdout.pipe(process.stdout);

    server.stderr.pipe(process.stderr);

    server.on("exit", (code) => {
      const codeMsg = (code) ? `with code ${code.toString()}` : "";
      console.log(` Admin server stopped ${codeMsg}`);
    });

    cb();

  });

};
