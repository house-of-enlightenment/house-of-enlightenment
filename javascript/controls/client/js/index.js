import React from "react";
import ReactDom from "react-dom";

import osc from "osc";
import App from "./components/App.jsx";

var oscPort = new osc.WebSocketPort({
    url: "ws://localhost:3032", // URL to your Web Socket server.
    metadata: true
});
oscPort.open();


oscPort.on("ready", function () {
  console.log('Websocket connected, rendering app');

  ReactDom.render(
    <App />,
    document.querySelector(".js-app-mount")
  );
});
