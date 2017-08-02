/**
 * @param  {String} message json message from the client (button pushed, fader moved)
 * @param  {Object} udpPort and instance of OSC.udpPort
 * @return {Object} an osc message to be sent to the python script
 *                   on port 7000
 */
module.exports = function parseClientMessage(json) {
  const data = JSON.parse(json);
  const address = `/input/${data.type}`; // eg. /input/button
  const args = getArgs(data);

  return{
    address: address,
    args: args
  };
};


/**
 * http://opensoundcontrol.org/spec-1_0
 * @param  {Object} data { stationId, type, id, value }
 * @return {Array} arguments array according to the osc spec
 */
function getArgs(data){

  // type: i = int32,  f = float32, s = OSC-string,  b = OSC-blob
  const defaultArgs = [
    {
      type: "i",
      value: data.stationId
    },
    {
      type: "i",
      value: data.id
    }
  ];

  // different types have different args
  switch(data.type){
    // add value to the fader
    case "fader":
      return defaultArgs.concat([{
        type: "i",
        value: parseInt(data.value)
      }]);

    // use the default args for button
    case "button":
    default:
      return defaultArgs;
  }
}
