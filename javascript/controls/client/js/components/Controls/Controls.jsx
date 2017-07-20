import React from "react";
import { func, number } from "prop-types";

import Button from "../Button/Button.jsx";
import Slider from "../Slider/Slider.jsx";

const propTypes = {
  id: number.isRequired,
  onButtonClick: func.isRequired,
  onSliderChange: func.isRequired
};


const Controls = ({ onButtonClick, onSliderChange }) => {

  return (
    <div className="controls">
      <Button onClick={() => onButtonClick("left")} direction="left" />
      <Slider onChange={onSliderChange}/>
      <Button onClick={() => onButtonClick("right")} direction="right" />
    </div>
  );

};

Controls.propTypes = propTypes;

export default Controls;
