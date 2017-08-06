# House of Enlightenment

https://douglasruuska.com/tower-of-light/

http://mikelambert.me/house-of-enlightenment

# Quick Start
## When you first install this repo
Make sure you have the latest LTS of node from https://nodejs.org/en/ (currently `v6.11.0`)
```
npm install -g gulp-cli // installs gulp cli globally (only needed once per computer)
npm install             // installs projects dependancies
gulp build-all          // compile the simulator, contorls, and hoe client files
```

## Javascript Simulator and OSC Controls
The repo contains a javascript simulator that listens for OPC information and renders the pixels in the browser.

Below is the most common command for starting the simulator. If you are not developing on the simulator, this is likely all you need. Upon launching, the server will be running on http://localhost:3034. For more information,  read [here](./javascript)

```
# Run with default layout file (`layout/hoeLayout.json`)
gulp hoe
```

## Run Python OPC light server
A python middlelayer is responsible for receiving input data via OSC, selecting which animations should be displayed, and pushing the current frames to the pixel controllers (beagle boards or the javascript simulator) via OPC.
For more information, including controlling and contributing animations and interacting with the server while it's running, read [here](./python)

```
# To run the python server with default settings, use:
python ./python/houseOfEnlightenment.py
```
To navigate between animations, you can type "next" or "scene <scene name>" into the console. You can also replicate button input with /input/button <station id> <button id>. For example "/input/button 1 4". *To exit, "quit" in prefered over an interrupt such as ctrl+c*

The defaults uses the [house of enlightenment layout file](./layout.hoeLayout.json) and the [local servers file](./layout/servers_local.json). This sends OPC socket messages with the pixel data to http://localhost:7890 (the javascript simulator server is listening for OPC messages on port `7890`) and OSC button control messages to http://localhost:57121. 

## Known Issues
- Currently if the python server crashes or exits via ctrl-C (instead of "quit"), it can cause trouble reconnecting to the javascript simulator on the next run. You'll need to restart the simulator to handle this.
- The simulator stores button state at the client side. For animations that light up buttons, you may need to refresh the client and then reinitialize the scene.


### BeagleBone LEDScape controller info
https://github.com/house-of-enlightenment/LEDscape
