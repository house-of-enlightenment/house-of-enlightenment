import React from "react";
import { func, oneOf } from "prop-types";


const propTypes = {
  id: oneOf(["left", "right"]),
  onClick: func.isRequired
};


const Button = ({ id, onClick }) => {

  return (
    <button onClick={onClick}>
      { id === "left" ? "<" : ">"}
    </button>
  );

};

Button.propTypes = propTypes;

export default Button;
