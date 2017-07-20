import React from "react";
import { func, oneOf } from "prop-types";


const propTypes = {
  onChange: func.isRequired
};


const Slider = ({ onChange }) => {

  const onSliderChange = (e) => {
    onChange(e.target.value);
  }

  return (
    <input type="range" orient="vertical" onChange={onSliderChange} />
  );

};

Slider.propTypes = propTypes;

export default Slider;
