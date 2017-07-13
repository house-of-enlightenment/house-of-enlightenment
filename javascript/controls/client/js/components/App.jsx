import React from "react";
import R from "ramda";

import Controls from "./Controls/Controls.jsx";

const App = () => {

  const onButtonClick = R.curry((controlsId, leftOrRight) => {
    console.log(controlsId, leftOrRight)
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
