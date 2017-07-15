import React from "react";
import R from "ramda";

import Controls from "./Controls/Controls.jsx";

const propTypes = {
  osc: func.isRequired,
};


const App = ({ osc }) => {

  const onButtonClick = R.curry((controlsId, leftOrRight) => {
    osc.send({
        address: "/button",
        args: [
	    {
		type: "i",
		value: controlsId
	    },	    
            {
                type: "s",
                value: leftOrRight
            },
        ]
    });
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

App.propTypes = propTypes

export default App;
