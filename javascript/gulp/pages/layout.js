const gulp = require("gulp");
const quench = require("../quench.js");
const spawn = require("child_process").spawn;
const runSequence = require("run-sequence");

const createCopyTask = require("../tasks/createCopyTask.js");
const createJsTask   = require("../tasks/createJsTask.js");
const createBrowserSyncTask = require("../tasks/createBrowserSyncTask.js");

module.exports = function layoutTask(projectRoot) {

  const layoutBuild = `${projectRoot}/javascript/layout-generator/build`;
  const layoutRoot = `${projectRoot}/javascript/layout-generator`;

  quench.maybeWatch("layout", [
    `${projectRoot}/layout-generator/generate/**`,
    `${projectRoot}/layout-generator/test/**`
  ]);


  gulp.task("layout", function(cb){

    // write the file
    gulp.task("write-layout", function(cb){
      return writeHoeLayout(projectRoot, cb);
    });


    createCopyTask("layout-copy-index", {
      src: `${layoutRoot}/test/index.html`,
      dest: layoutBuild
    });

    // copy the csv/json data files to the build directory so
    // we can fetch them from the browser
    createCopyTask("layout-copy-data", {
      src: `${projectRoot}/layout/files/**/*.{json,csv}`,
      dest: `${layoutBuild}/data`
    });


    createJsTask("layout-js", {
      dest: `${layoutBuild}/js/`,
      files: [
        {
          gulpTaskId: "js-layout",
          entry: `${layoutRoot}/test/index.js`,
          filename: "index.js",
          watch: [
            `${layoutRoot}/test/**/*.js`
          ]
        }
      ]
    });


    createBrowserSyncTask("layout-browser-sync", {
      files: layoutBuild + "/**",
      server: layoutBuild
    });


    if (quench.isWatching()){
      return runSequence(
        ["layout-js", "layout-copy-index", "layout-copy-data"],
        "layout-browser-sync"
      );
    }
    else {
      return runSequence("write-layout");
    }

  });

};


// genreate hoeLayout.json
function writeHoeLayout(projectRoot, cb) {

  // run the node script to generated hoeLayout.json
  const generate = spawn("node", ["writeHoeLayout.js"], {
    cwd: `${projectRoot}/javascript/layout-generator/generate`
  });

  generate.stdout.pipe(process.stdout);

  generate.stderr.pipe(process.stderr);

  // when the script is done
  generate.on("exit", (code) => {
    cb();
  });

}
