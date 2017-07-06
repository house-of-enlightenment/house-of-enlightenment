# House of Enlightenment

https://douglasruuska.com/tower-of-light/

http://mikelambert.me/house-of-enlightenment


## When you first install this repo
Make sure you have the latest LTS of node from https://nodejs.org/en/ (currently `v6.11.0`)
```
npm install -g gulp-cli // installs gulp cli globally
cd javascript
npm install             // installs projects dependancies
gulp simulator:build    // compile the simulator client files
```


## Run the simulator
### Run with default layout file (`hoeLayout.json`)
```
cd javascript
gulp simulator
```

server will be running on http://localhost:3030

### To specify layout file
```
cd javascript
gulp simulator --layout ./layout/spire-large.json
```


### To run simulator without gulp
```
node ./javascript/simulator/server/server.js --layout layout/hoeLayout.json
```
open browser to http://localhost:3030


## Run OPC light server
```
python ./python/spireControllerWithAnimations.py -l ./layout/hoeLayout.json -s 127.0.0.1:7890
```
The above sends OPC socket messages to http://localhost:7890 (the simulator server is listening for OPC messages on port `7890`)
