const gulp = require("gulp");
const quench = require("../quench.js");
const spawn = require("child_process").spawn;


module.exports = function layoutTask(config, env) {

  quench.registerWatcher("layout", `${config.root}/layout/scripts/generateLayout.js`);

  // genreate hoeLayout.json
  gulp.task("layout", function(cb) {

    // run the node script to generated hoeLayout.json
    const generate = spawn("node", ["nodeGenerateLayout.js"], {
      cwd: `${config.root}/javascript/layout-generator`
    }, cb);

    generate.stdout.on("data", (data) => console.log(data.toString()));

    generate.stderr.on("data", (data) => console.error(data.toString()));

    generate.on("exit", (code) =>
      console.log("server stopped with code " + code.toString()));

  });

}
