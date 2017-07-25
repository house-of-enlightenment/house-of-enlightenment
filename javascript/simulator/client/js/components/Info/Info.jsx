import React from "react";
import classNames from "classnames";

export default class Info extends React.Component {

  state = {
    isOpen: false
  }

  componentWillUnmount = () => {
    window.removeEventListener("click", this.handleClickAway, true);
    window.removeEventListener("keydown", this.handleKeydown);
  }

  componentDidUpdate = (prevProps, prevState) => {
    if (this.state.isOpen){
      window.addEventListener("click", this.handleClickAway, true);
      window.addEventListener("keydown", this.handleKeydown);
    }
    else {
      window.removeEventListener("click", this.handleClickAway, true);
      window.removeEventListener("keydown", this.handleKeydown);
    }
  }

  handleKeydown = (e) => {
    const keyCode = e.which || e.keyCode || e.code || 0;

    // esc
    if (keyCode === 27){
      this.setState({ isOpen: false });
    }
  }

  handleClickAway = (e) =>{
    this.setState({ isOpen: false });
  }

  handleClick = (e) => {
    this.setState({ isOpen: true });
  }

  render(){

    const { isOpen } = this.state;

    return (
      <div className="info">
        <div className="info__icon" onClick={this.handleClick}>i</div>

        <div className={classNames("info__popup-holder", { "is-hidden" : !isOpen })}>
          <div className="info__popup">
            <p>Click/drag with mouse to look around like a first person shooter video game.</p>
            <p>
              Use
              <span className="key">W</span>
              <span className="key">A</span>
              <span className="key">S</span>
              <span className="key">D</span>
              on your keyboard to run around.
            </p>
            <p className="info__mappings">
              <span className="info__mapping"><span className="key">W</span>=forward</span>
              <span className="info__mapping"><span className="key">A</span>=left</span>
              <span className="info__mapping"><span className="key">S</span>=backward</span>
              <span className="info__mapping"><span className="key">D</span>=right</span>
            </p>
            <p>You can also go up and down.</p>
            <p className="info__mappings">
              <span className="info__mapping"><span className="key">R</span>=up</span>
              <span className="info__mapping"><span className="key">F</span>=down</span>
            </p>
          </div>
        </div>
      </div>
    );
  }
}
