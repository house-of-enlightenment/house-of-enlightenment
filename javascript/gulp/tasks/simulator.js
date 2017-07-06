const gulp = require("gulp");
const spawn = require("child_process").spawn
const R = require("ramda");

module.exports = function simulatorTask(config, env) {

  gulp.task("simulator", function(cb){

    const layout = R.path(["yargs", "layout"], config) || "layout/hoeLayout.json";

    // run the node server
    // https://stackoverflow.com/questions/10232192/exec-display-stdout-live
    const server = spawn("node",
      ["javascript/simulator/server/server.js", "--layout", layout],
      { cwd: `${config.root}` }
    );

    server.stdout.pipe(process.stdout);

    server.stderr.pipe(process.stderr);

    server.on("exit", (code) => {
      console.log("server stopped with code " + code.toString());
    })

  });

}
