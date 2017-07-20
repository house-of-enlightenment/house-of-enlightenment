import React from "react";
import { func, number } from "prop-types";

import Button from "../Button/Button.jsx";
import Fader from "../Fader/Fader.jsx";

const propTypes = {
  id: number.isRequired,
  onButtonClick: func.isRequired,
  onFaderChange: func.isRequired
};


const Controls = ({ onButtonClick, onFaderChange }) => {

  return (
    <div className="controls">
      <Button id="left" onClick={() => onButtonClick(0)} />
      <Fader id="middle" onChange={onFaderChange(0)} />
      <Button id="right" onClick={() => onButtonClick(1)} />
    </div>
  );

};

Controls.propTypes = propTypes;

export default Controls;
