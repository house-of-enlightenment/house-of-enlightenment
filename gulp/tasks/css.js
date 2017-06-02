const gulp         = require("gulp");
const quench       = require("../quench.js");
const sass         = require("gulp-sass");
const autoprefixer = require("gulp-autoprefixer");
const rename       = require("gulp-rename");
const debug        = require("gulp-debug");
const header       = require("gulp-header");
const concat       = require("gulp-concat");
const sourcemaps   = require("gulp-sourcemaps");

module.exports = function cssTask(config, env) {

    // css settings
    const cssConfig = {
        src: [
            config.root + "/scss/**/*.scss",
            config.root + "/js/**/*.scss"
        ],
        dest: config.dest + "/css/",

        filename: "index.css",

        sass: {
            outputStyle: env.development() ? "expanded" : "compressed"
        },

        autoprefixer: {
            browsers: ["> 1%", "last 2 versions", "Firefox ESR", "Opera 12.1", "ie >= 9"]
        }
    };

    // register the watch
    quench.registerWatcher("css", cssConfig.src);


    /* css task */
    gulp.task("css", function() {

        const gulpCss = gulp.src(cssConfig.src)
            .pipe(quench.drano())
            .pipe(sourcemaps.init())
            .pipe(sass(cssConfig.sass))
            .pipe(autoprefixer(cssConfig.autoprefixer))
            .pipe(concat(cssConfig.filename, {newLine: ""}))
            .pipe(rename({
                suffix: "-generated"
            }));

        // only add the header text if this css isn't compressed
        if (cssConfig.sass && cssConfig.sass.outputStyle !== "compressed") {
            gulpCss.pipe(header("/* This file is generated.  DO NOT EDIT. */ \n"));
        }

        return gulpCss
            .pipe(sourcemaps.write("./"))
            .pipe(gulp.dest(cssConfig.dest))
            .pipe(debug({title: "css:"}));
    });
};
