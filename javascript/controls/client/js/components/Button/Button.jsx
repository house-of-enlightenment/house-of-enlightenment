import React from "react";
import { func, oneOf } from "prop-types";


const propTypes = {
  id: oneOf(["0", "1", "2", "3", "4"]),
  onClick: func.isRequired
};


const Button = ({ id, onClick }) => {

  return (
    <button onClick={onClick}>
      { id }
    </button>
  );

};

Button.propTypes = propTypes;

export default Button;
