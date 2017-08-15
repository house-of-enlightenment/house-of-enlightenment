import React from "react";
import { object } from "prop-types";
import R from "ramda";

import Controls from "./Controls/Controls.jsx";

function getButtonColor(id){
  switch (id){
    case 0:
      return "red";
    case 1:
      return "green";
    case 2:
      return "blue";
    case 3:
      return "yellow";
    default:
      return "white";
  }
}


export default class App extends React.Component {

  static propTypes = {
    ws: object.isRequired
  };

  state = {
    controls: R.range(0, 6).map(i => ({
      buttons: R.range(0, 5).map(j => ({
        isDisabled: false,
        color: getButtonColor(j)
      })),
      faders: R.range(0, 1).map(k => ({
        value: 0
      }))
    }))
  };

  componentDidMount = () => {
    const { ws } = this.props;

    // currently, there is only one type of message coming back
    // to toggle a button
    ws.onmessage = (message) => {

      const { stationId, buttonId, onOrOff } = JSON.parse(message.data);

      const { controls } = this.state;

      // create a lens to look deep inside the controls stucture to find the
      // current button disabled state
      const buttonLens = R.lensPath([ stationId, "buttons", buttonId, "isDisabled" ]);

      // see server/parseOscMessage.js
      const getDisabledState = function(){
        switch (onOrOff){
          case 0:
            return true;
          case 1:
            return false;
          case 2:
            return !R.view(buttonLens, controls); // toggle
        }
      };

      const newControls = R.set(buttonLens, getDisabledState(), controls);

      this.setState({
        controls: newControls
      });
    };
  }

  onButtonClick = R.curry((stationId, buttonId) => {

    console.log("button", stationId, buttonId);

    const { ws } = this.props;

    ws.send(JSON.stringify({
      stationId: stationId,
      type: "button",
      id: buttonId
    }));
  });


  onFaderChange = R.curry((stationId, faderId, value) => {

    console.log("fader", stationId, faderId, value);

    const { ws } = this.props;
    const { controls } = this.state;

    const faderLens = R.lensPath([ stationId, "faders", faderId, "value" ]);

    const newControls = R.set(faderLens, value, controls);

    this.setState({
      controls: newControls
    });

    ws.send(JSON.stringify({
      stationId: stationId,
      type: "fader",
      id: faderId,
      value
    }));
  });


  render = () => {

    const { controls } = this.state;

    return (
      <div className="controls-set">
        {
          controls.map((c, i) => (
            <Controls key={i}
              id={i}
              buttons={c.buttons}
              faders={c.faders}
              onButtonClick={this.onButtonClick(i)}
              onFaderChange={this.onFaderChange(i)}
            />
          ))
        }
      </div>
    );
  }

}
