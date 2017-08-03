import React from "react";
import ReactDom from "react-dom";
import App from "./components/App.jsx";


const ws = new WebSocket("ws://localhost:4040");

ws.onopen = function (event) {
  console.log("controls websocket connection made tp ws://localhost:4040");
  ReactDom.render(
    <App ws={ws} />,
    document.querySelector(".js-controls-mount")
  );
};

ws.onmessage = function (event) {
  console.log("websocket message", event.data);
};
