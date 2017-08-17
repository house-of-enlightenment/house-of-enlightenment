const R = require("ramda");


/**
 * parse a message from the python script
 * @param  {Buffer} data a buffer of a string of 5 numbers, eg "10111"
 * @param  {Number} stationId 0-5
 * @return {Array} an array of numbers, eg. [0, 1, 1, 1, 1]
 *   0 means off, 1 means on
 */
module.exports = function parseMessage({ data, stationId }){

  return JSON.stringify({
    stationId,
    buttonStates: data.toString().split("").map(Number)
  });

};
