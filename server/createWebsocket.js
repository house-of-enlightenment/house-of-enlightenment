const WebSocket = require("ws");

module.exports = function createWebsocket(server){

  const wss = new WebSocket.Server({ server });

  wss.on("connection", function connection(ws) {

    ws.on("message", function incoming(json){

      const actions = getActionsMap(ws, handleMessage);

      /**
       * Look in the actions lookup and execute if the msgType is there
       */
      function handleMessage(message){

        const action = actions[message.msgType];

        if (typeof(action) === "function"){
          action(message.payload);
        }
        else {
          console.log(`message not recognized: ${JSON.stringify(message)}`);
        }

      }

      /**
       * Actual code to handle the message
       */
      console.log("received: %s", json);

      try {

        const message = JSON.parse(json);

        handleMessage(message);
      } catch(e) {
        console.log("can't parse json!");
      }

    });

  });
};


function getActionsMap(ws){
  /**
   * Lookup of actions
   */
  const actions = {

  };

  return actions;
}
