import React from "react";
import { func, number } from "prop-types";

import Button from "../Button/Button.jsx";

const propTypes = {
  id: number.isRequired,
  onButtonClick: func.isRequired
};


const Controls = ({ onButtonClick }) => {

  return (
    <div className="controls">
      <Button onClick={() => onButtonClick("left")} direction="left" />
      <Button onClick={() => onButtonClick("right")} direction="right" />
    </div>
  );

};

Controls.propTypes = propTypes;

export default Controls;
