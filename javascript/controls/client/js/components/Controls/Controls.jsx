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
      <div className="buttonSection">
        <Button id="0" onClick={() => onButtonClick(0)} />
        <Button id="1" onClick={() => onButtonClick(1)} />
        <Button id="2" onClick={() => onButtonClick(2)} />
        <Button id="3" onClick={() => onButtonClick(3)} />
        <Button id="4" onClick={() => onButtonClick(4)} />
      </div>
      <div className="faderSection">
        <Fader id="0" onChange={onFaderChange(0)} />
        <Fader id="1" onChange={onFaderChange(1)} />
        <Fader id="2" onChange={onFaderChange(2)} />
        <Fader id="3" onChange={onFaderChange(2)} />
      </div>
    </div>
  );

};

Controls.propTypes = propTypes;

export default Controls;
