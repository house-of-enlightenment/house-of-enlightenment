import React from "react";
import { object } from "prop-types";
import R from "ramda";

import Controls from "./Controls/Controls.jsx";

function getButtonColor(id){
  switch (id){
    case 0:
      return "yellow";
    case 1:
      return "green";
    case 2:
      return "white";
    case 3:
      return "red";
    default:
      return "blue";
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

      const { stationId, buttonStates } = JSON.parse(message.data);

      const { controls } = this.state;

      // create a lens to look at the buttons for this stationId
      const buttonLens = R.lensPath([ stationId, "buttons" ]);

      // see server/parseMessage.js
      const getDisabledState = function(onOrOff){
        switch (onOrOff){
          case 0:
            return true;
          case 1:
            return false;
        }
      };

      // update the array of buttons by merging in isDisabled
      const updateButtons = buttons => {
        return buttons.map((button, i) => {
          return R.merge(button, {
            isDisabled: getDisabledState(buttonStates[i])
          });
        });
      };

      const newControls = R.over(buttonLens, updateButtons, controls);

      this.setState({
        controls: newControls
      });
    };
  }

  onButtonClick = R.curry((stationId, buttonId) => {

    const { ws } = this.props;

    const message = JSON.stringify({
      stationId: stationId,
      type: "button",
      id: buttonId
    });

    console.log(message);

    ws.send(message);
  });


  onFaderChange = R.curry((stationId, faderId, value) => {

    const { ws } = this.props;
    const { controls } = this.state;

    const faderLens = R.lensPath([ stationId, "faders", faderId, "value" ]);

    const newControls = R.set(faderLens, value, controls);

    this.setState({
      controls: newControls
    });

    const message = JSON.stringify({
      stationId: stationId,
      type: "fader",
      id: faderId,
      value
    });

    console.log(message);

    ws.send(message);
  });


  render = () => {

    const { controls } = this.state;

    return (
      <div style={{ textAlign: "center" }}>
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
      </div>
    );
  }

}
