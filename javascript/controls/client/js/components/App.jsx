import React from "react";
import { object } from "prop-types";
import R from "ramda";

import Controls from "./Controls/Controls.jsx";

const propTypes = {
  ws: object.isRequired
};

const App = ({ ws }) => {

  const onButtonClick = R.curry((stationId, buttonId) => {

    console.log("button", stationId, buttonId);

    ws.send(JSON.stringify({
      stationId: stationId,
      type: "button",
      id: buttonId
    }));
  });

  const onFaderChange = R.curry((stationId, faderId, value) => {

    console.log("fader", stationId, faderId, value);

    ws.send(JSON.stringify({
      stationId: stationId,
      type: "fader",
      id: faderId,
      value
    }));
  });


  return (
    <div className="controls-set">
      {R.range(0, 6).map(i => (
        <Controls key={i}
          id={i}
          onButtonClick={onButtonClick(i)}
          onFaderChange={onFaderChange(i)}
        />
      ))}
    </div>
  );

};

App.propTypes = propTypes;

export default App;
