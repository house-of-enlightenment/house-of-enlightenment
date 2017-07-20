import React from "react";
import { func, oneOf } from "prop-types";


const propTypes = {
  onClick: func.isRequired,
  direction: oneOf(["left", "right"])
};


const Button = ({ onClick, direction }) => {

  return (
    <button onClick={onClick}>
      { direction === "left" ? "<" : ">"}
    </button>
  );

};

Button.propTypes = propTypes;

export default Button;
