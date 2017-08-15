import React from "react";
import classNames from "classnames";
import { bool, func, number, oneOf } from "prop-types";


const propTypes = {
  id: number.isRequired,
  onClick: func.isRequired,
  isDisabled: bool,
  color: oneOf(["red", "green", "blue", "yellow", "white"])
};

const defaultProps = {
  color: "white"
};


const Button = ({ id, onClick, color, isDisabled }) => {

  const buttonClasses = classNames(`button--${color}`, {
    "is-disabled": isDisabled
  });

  return (
    <button onClick={onClick} className={buttonClasses}>
      {/* { id } */}
    </button>
  );

};

Button.propTypes = propTypes;
Button.defaultProps = defaultProps;

export default Button;
