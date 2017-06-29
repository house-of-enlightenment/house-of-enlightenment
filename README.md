## House of Enlightenment

https://douglasruuska.com/tower-of-light/

http://mikelambert.me/house-of-enlightenment


### when you first install this repo
```
npm install -g gulp-cli // installs gulp cli globally
npm install             // installs projects dependancies
gulp build              // compile the simulator client files
```

### run the simulator
```
node ./server/server.js --layout ./app/layout/layout.json
```
open browser to http://localhost:3030


### run light server
from https://github.com/anthonyn/hoeTemp
```
./python/spireControllerWithAnimations.py -l ../house-of-enlightenment/app/layout/layout.json  -s 127.0.0.1:7890
```
The above sends OPC socket messages to http://localhost:7890


### to develop the simulator
```
gulp
```
will start the simulator with default layout and compile simulator client code from `/app`.  This will also start watchers that will reload the browser when files in `/app` are saved.

Open browser to http://localhost:3000
