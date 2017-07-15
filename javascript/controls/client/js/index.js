import React from "react";
import ReactDom from "react-dom";
import App from "./components/App.jsx";


const ws = new WebSocket('ws://localhost:4040');

ws.onopen = function (event) {
  console.log('websocket connection made, render page');
  ReactDom.render(
    <App ws={ws} />,
    document.querySelector(".js-app-mount")
  );
};
