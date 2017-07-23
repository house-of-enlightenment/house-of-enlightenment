# House of Enlightenment

https://douglasruuska.com/tower-of-light/

http://mikelambert.me/house-of-enlightenment

## When you first install this repo
Make sure you have the latest LTS of node from https://nodejs.org/en/ (currently `v6.11.0`)
```
npm install -g gulp-cli // installs gulp cli globally (only needed once per computer)
npm install             // installs projects dependancies
gulp simulator          // compile the simulator client files
gulp controls           // compile the controls client files
```

## Javascript Simulator and OSC Controls
The repo contains a javascript simulator that listens for OPC information and renders the pixels in the browser.

Below are the most common commands for starting the simulator. Upon launching, the server will be running on http://localhost:3030. For more information, read [here](./javascript/simulator)

```
# Run with default layout file (`hoeLayout.json`)
gulp simulator-server

# To specify a layout file
gulp simulator-server --layout ./layout/spire-large.json

# To run simulator without gulp
node ./javascript/simulator/server/server.js --layout layout/hoeLayout.json
```

### Run controls page
To send OSC commands from the browser, launch the javascript controls server. The server will be running on http://localhost:3032. For more information, read [here](./javascript/controls)
```
gulp controls-server
```

## Run Python OPC light server
A python middlelayer is responsible for receiving input data via OSC, selecting which animations should be displayed, and pushing the current frames to the pixel controllers (beagle boards or the javascript simulator) via OPC.
For more information, including controlling and contributing animations and interacting with the server while it's running, read [here](./python)

Startup Commands:
```
# To run the python server with default settings, use:
python ./python/houseOfEnlightenment.py
# To run with customized layout or server, use:
python ./python/houseOfEnlightenment.py -l ../layout/hoeLayout.json -s 127.0.0.1:7890
```
The defaults uses the [house of enlightenment layout file](./layout.hoeLayout.json) and the sends OPC socket messages to http://localhost:7890 (the javascript simulator server is listening for OPC messages on port `7890`)
