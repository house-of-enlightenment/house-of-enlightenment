import React from "react";
import { func, number } from "prop-types";


const propTypes = {
  id: number.isRequired,
  onChange: func.isRequired,
  value: number.isRequired
};


const Fader = ({ onChange, value }) => {

  const onFaderChange = (e) => {
    onChange(Number(e.target.value));
  };

  return (
    <input
      className="fader"
      type="range"
      orient="horizontal"
      onChange={onFaderChange}
      value={value}
    />
  );

};

Fader.propTypes = propTypes;

export default Fader;
