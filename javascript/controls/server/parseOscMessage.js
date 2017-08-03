const R = require("ramda");

/**
 * example oscMessage
 *  {
 *    address: "/button",
 *    args: [
 *      { type: "i", value: 0 },
 *      { type: "i", value: 2 },
 *      { type: "i", value: 0}
 *    ]
 *  }
 *
 *   args:
 *     1st: {Number} stationId
 *     2nd: {Number} buttonId
 *     3rd: {Number} onOrOff - a number 0, 1, or 2
 *                   0 = on
 *                   1 = off
 *                   2 = toggle
 *
 */
// paramters: https://www.npmjs.com/package/osc#events
module.exports = function parseOscMessage(oscMessage, timeTag, info){
  // console.log("oscMessage from python:, ", oscMessage);

  const [ stationId, buttonId, onOrOff ] = R.map(R.prop("value"), oscMessage.args);

  const message = {
    stationId, buttonId, onOrOff
  };

  return JSON.stringify(message);
};
