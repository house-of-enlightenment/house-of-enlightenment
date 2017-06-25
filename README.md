## House of Enlightenment

https://douglasruuska.com/tower-of-light/

http://mikelambert.me/house-of-enlightenment

## Quick start
### run web server
```
npm install -g gulp-cli // installs gulp cli globally
npm install             // installs projects dependancies
gulp                    // compiles files and starts server
```
open browser to `http://localhost:3000`

### run light server
from https://github.com/anthonyn/hoeTemp
```
./python/spireControllerWithAnimations.py -l ../house-of-enlightenment/app/layout/layout.json  -s 127.0.0.1:7890
```

### Gulp
See gulp [readme.md](./gulp/readme.md) for setup.

The entry `gulpfile.js` is located in `gulp` and all gulp commands need to be run from this directory. There is also a proxy `gulpfile.js` at the project root, which can run all the same commands.

Available commands are
 * `gulp` - will run dev build with watchers
 * `gulp build` - will run dev _without_ watchers.
 * `gulp prod` - will run production build without watchers
 * `gulp [task]` - where task is loaded in `gulpfile.js`.  eg. `css`, `js`

The watcher will also start a [browserSync](https://browsersync.io/) server.  The console will tell you the exact port, but it usually runs on [http://localhost:3000/](http://localhost:3000/).  


### Javascript
There are 2 types of Javascript files that are generated via the gulp build.

#### 1. Application scripts
All javascript source files are located in `/js/`.

All generated files will be compiled into `/build/js` and have `-generated` appended to the end of the filename.

eg. `/js/index.js` > `/build/js/index-generated.js`

By default, `index.js` is the only entry file. Multiple entry files can be specified in `/gulp/tasks/js.js`.

ES6 modules are used to import other files into these entry point files. eg:

`import React from "react";`  
`import DataProfile from "../components/DataProfile/DataProfile.jsx";`



#### 2. 3rd party scripts
Generated into `/build/js/libraries-generated.js`

3rd party Javascript dependancies are included via gulp and `package.json` in the root of the project.  To add a new javascript dependency, from the project root, run eg. `npm install --save react`.  Then, in your application script file, use eg. `import React from "react";` to include the dependency by the package name.


### CSS
Gulp will compile all scss files in the project and concat them into a single file `/build/css/index-generated.css`.

[BEM](https://css-tricks.com/bem-101/) methodology is loosely used for class naming. In general, every new Block element should get a new file in `/scss/`.

For more information, refer to [http://wiki.velir.com/index.php?title=Semantics_Using_BEM/SMACSS](http://wiki.velir.com/index.php?title=Semantics_Using_BEM/SMACSS)


### Images
All image are located in `/img/` and can be accessed in the code via the url `/img/`.

### SVG sprite
An svg sprite is generated with all the svgs located in `/img/svg-sprite/`. Using `<use>` is fairly limited, so only use the svg-sprite if it fits your needs. Otherwise, just put the svg's in `img/`.

To use the svg-sprite, put the svg's in this directory.  eg. `img/svg-sprite/my-icon.svg`. All these files will be compiled into `img/svg-sprite.svg`.

In html: `<svg><use xlink:href="/img/svg-sprite.svg#my-icon"></use></svg>`

In css: `svg { fill: BlanchedAlmond; }`
