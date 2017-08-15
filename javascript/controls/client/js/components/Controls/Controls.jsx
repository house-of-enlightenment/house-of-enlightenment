import React from "react";
import { array, func, number } from "prop-types";

import Button from "../Button/Button.jsx";
import Fader from "../Fader/Fader.jsx";

const propTypes = {
  id: number.isRequired,
  buttons: array.isRequired,
  faders: array.isRequired,
  onButtonClick: func.isRequired,
  onFaderChange: func.isRequired
};


const Controls = ({ buttons, faders, onButtonClick, onFaderChange }) => {

  return (
    <div className="controls">
      <div className="controls__buttons buttons">
        {buttons.map((button, i) => {
          const { isDisabled, color } = button;

          return (
            <Button key={i}
              id={i}
              isDisabled={isDisabled}
              onClick={() => onButtonClick(i)}
              color={color}
            />
          );

        })}
      </div>
      <div className="controls__faders">
        {faders.map((fader, i) => {
          const { value } = fader;

          return (
            <Fader key={i}
              id={i}
              value={value}
              onChange={onFaderChange(i)}
            />
          );
        })}

      </div>
    </div>
  );

};

Controls.propTypes = propTypes;

export default Controls;
