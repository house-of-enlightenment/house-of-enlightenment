import React from "react";
import { func, string } from "prop-types";


const propTypes = {
  id: string.isRequired,
  onChange: func.isRequired
};


const Fader = ({ onChange }) => {

  const onFaderChange = (e) => {
    onChange(e.target.value);
  };

  return (
    <input type="range" orient="horizontal" onChange={onFaderChange} />
  );

};

Fader.propTypes = propTypes;

export default Fader;
