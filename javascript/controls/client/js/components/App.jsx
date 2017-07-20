import React from "react";
import { object } from "prop-types";
import R from "ramda";

import Controls from "./Controls/Controls.jsx";

const propTypes = {
  ws: object.isRequired
};

const App = ({ ws }) => {

  const onButtonClick = R.curry((controlsId, leftOrRight) => {

    console.log(controlsId, leftOrRight);

    ws.send(JSON.stringify({
      controlsId: controlsId,
      type: "button",
      leftOrRight: leftOrRight
    }));
  });

  const onSliderChange = R.curry((controlsId, value) => {

    console.log("slider", controlsId, value);

    ws.send(JSON.stringify({
      controlsId: controlsId,
      type: "slider"
    }));
  });


  return (
    <div className="controls-set">
      {R.range(0, 6).map(i => (
        <Controls key={i}
          id={i}
          onButtonClick={onButtonClick(i)}
          onSliderChange={onSliderChange(i)}
        />
      ))}
    </div>
  );

};

App.propTypes = propTypes;

export default App;
