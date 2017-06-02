Gulp Usage
==========

Once per computer
------------------
1. Install LTS version of node from [https://nodejs.org/](https://nodejs.org/)
2. Install gulp globally:  
   `npm install -g gulp-cli`


Once per project
----------------
This will add gulp to this project and all the other packages that it
needs to compile css, etc. All these dependancies get installed to the
`node_modules` folder.  If things get messed up, you can delete this
folder and reinstall.

1. Navigate to the folder containing `package.json`:  
   either the the project root, or `cd /gulp`.
2. Install dependancies via
   `npm install`


Running bundled tasks
---------------------

1. Navigate to the folder containing `gulpfile.js`:  
    either `cd /gulp`, or at the project root.

2. Run `gulp` or `gulp [task]`, eg. `gulp build`

The actual gulp tasks will vary by project. Look in `/gulpfile.js` for specific [`gulp.task()`](https://github.com/gulpjs/gulp/blob/master/docs/API.md#gulptaskname--deps--fn) declarations. The tasks defined here will run multiple sub-tasks (from the `/tasks` folder) as specified by the `tasks` key in the `config` object passed to `build()`.  See [quench.js](./quench.js) for details and example below. In general, the following should be defined in `/gulpfile.js`:
  * `gulp` (default task)
    Will run the development task that will watch for changes in the source files.
    For example, if you change index.scss, gulp will run the css task to
    compile the sass to css automatically. You will see this happen in your
    terminal.
  * `gulp build` Will run the dev task _without_ watcher.  
  * `gulp prod` Will run the production task that will not watch, and it will compile the files for
    production (minified, etc).  This should be used for Continuous Integration.

Example bundled task
--------------------
Defined in `/gulpfile.js`. See [quench.js](./quench.js) for details.
```
gulp.task("build", function(next){

    const config = R.merge(defaults, {
        env   : "development",
        watch : false,
        tasks : ["js", "js-libraries", "css", "svg-sprite"]
    });

    quench.build(config, next);

});
```

Running single tasks
--------------------
In `gulpfile.js`, add a line:
    `quench.singleTasks(defaultConfig);`

This will watch command line arguments so it's possible to run a single task
defined in `/tasks/`.  eg. `/tasks/css.js`
```
    $ gulp css                  // will use the environment from config
    $ gulp css --env production // will use the production environment
    $ gulp css --watch          // will override the watch configuration
    $ gulp css js               // will run both css and js tasks
```


Task files
----------
Individual tasks defined in `/tasks/`.  eg `/tasks/css.js`.  See documentation in [quench.js](./quench.js).
