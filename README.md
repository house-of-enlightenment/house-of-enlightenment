# House of Enlightenment

https://douglasruuska.com/tower-of-light/

http://mikelambert.me/house-of-enlightenment


## When you first install this repo
Make sure you have the latest LTS of node from https://nodejs.org/en/ (currently `v6.11.0`)
```
npm install -g gulp-cli // installs gulp cli globally
npm install             // installs projects dependancies
gulp simulator:build    // compile the simulator client files
```


## Run the simulator
### Run with default layout file (`hoeLayout.json`)
From the root directory:
```
gulp simulator
```

server will be running on http://localhost:3030

### To specify layout file
```
gulp simulator --layout ./layout/spire-large.json
```


### To run simulator without gulp
```
node ./simulator/server/server.js --layout layout/hoeLayout.json
```
open browser to http://localhost:3030


## Run OPC light server
```
python ./python/spireControllerWithAnimations.py -l ./layout/hoeLayout.json -s 127.0.0.1:7890
```
The above sends OPC socket messages to http://localhost:7890 (the simulator server is listening for OPC messages on port `7890`)


## To develop the simulator
```
gulp
```
This will start the simulator with default layout and compile simulator client code from `/app`.  This will also start watchers that will reload the browser when files in `/app` are saved.

Open browser to http://localhost:3000
