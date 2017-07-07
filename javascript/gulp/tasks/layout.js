const gulp = require("gulp");
const quench = require("../quench.js");
const spawn = require("child_process").spawn;


module.exports = function layoutTask(config, env) {

  quench.registerWatcher("layout", [
      `${config.root}/layout-generator/**`
  ]);

  // genreate hoeLayout.json
  gulp.task("layout", function(cb) {

    // run the node script to generated hoeLayout.json
    const generate = spawn("node", ["nodeGenerateLayout.js"], {
      cwd: `${config.root}/javascript/layout-generator`
    });

    generate.stdout.pipe(process.stdout);

    generate.stderr.pipe(process.stderr)

    // when the script is done
    generate.on("exit", (code) => {
      cb();
    });

  });

}
