const gulp   = require("gulp");
const quench = require("../quench.js");
const debug  = require("gulp-debug");

module.exports = function copyTask(config, env) {

    // copy files settings
    const copy = {
        src: [
            config.root + "/index.html"
        ],
        dest: config.dest
    };

    // register the watch
    quench.registerWatcher("copy", copy.src);


    /* copy files */
    gulp.task("copy", function(next) {

        return gulp.src(copy.src, { base: config.root })
            .pipe(quench.drano())
            .pipe(gulp.dest(copy.dest))
            .pipe(debug({title: "copy:"}));
    });
};
