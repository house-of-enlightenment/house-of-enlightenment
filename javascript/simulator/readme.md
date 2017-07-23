# simulator

## To compile client code
```
gulp simulator
```

## To run the simulator
The following will start the simulator server with the default layout file (`hoeLayout.json`) and start a server on http://localhost:3030
```
gulp simulator-server
```

You can specify an different layout file
```
gulp simulator-server --layout ./layout/spire-large.json
```


## To run simulator without gulp
```
node ./javascript/simulator/server/server.js --layout layout/hoeLayout.json
```


## To develop the simulator
The following will start the simulator with default layout and compile simulator client code from `/javascript/simulator/client`.  This will also start watchers that will reload the browser when files in `/javascript/simulator/client` are saved.
```
gulp simulator --watch
```

A browser-sync server will be running at http://localhost:3000
