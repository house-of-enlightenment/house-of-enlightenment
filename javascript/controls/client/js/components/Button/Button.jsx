import React from "react";
import classNames from "classnames";
import { func, oneOf } from "prop-types";


const propTypes = {
  id: oneOf(["0", "1", "2", "3", "4"]),
  onClick: func.isRequired
};


const Button = ({ id, onClick }) => {

  const buttonClasses = classNames(getButtonColorClass(id), {
    "is-disabled": Math.random() > 0.5
  });



  return (
    <button onClick={onClick} className={buttonClasses}>
      {/* { id } */}
    </button>
  );

};


function getButtonColorClass(id){

  console.log("ID", id);

  switch (id){
    case "0":
      return "button--red";
    case "1":
      return "button--green";
    case "2":
      return "button--blue";
    case "3":
      return "button--yellow";
    default:
      return "button--white";

  }

}

Button.propTypes = propTypes;

export default Button;
