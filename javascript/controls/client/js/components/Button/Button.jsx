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
    <div className={`button ${buttonClasses}`}>
      <button onClick={onClick}>
        {/* { id } */}
      </button>
    </div>
  );

};

Button.propTypes = propTypes;
Button.defaultProps = defaultProps;

export default Button;
