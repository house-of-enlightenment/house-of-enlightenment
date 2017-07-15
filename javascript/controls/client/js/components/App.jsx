import React from "react";
import R from "ramda";

import Controls from "./Controls/Controls.jsx";


const App = ({ ws }) => {

  const onButtonClick = R.curry((controlsId, leftOrRight) => {
    console.log(controlsId, leftOrRight)
    ws.send(JSON.stringify({controlsId: controlsId, leftOrRight: leftOrRight}));
  });


  return (
    <div className="controls-set">
      {R.range(0, 6).map(i => (
        <Controls key={i}
          id={i}
          onButtonClick={onButtonClick(i)}
        />
      ))}
    </div>
  );

};


export default App;
