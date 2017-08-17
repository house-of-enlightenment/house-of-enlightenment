
/**
 * The OPC message from python are a buffer of number in OPC format
 * The first 3rd and 4th byte tell the length of the data, so one message
 * is those first 4 byte + the data.  The python server might send it in
 * "chunks" so this function will keep track of what data we have so far
 * and only call "onComplete" when we have all of the data
 * @param  {Function} onComplete a callback function to call when we finally
 *   have all the data.  function(data) where data is the entire OPC message
 * @return {Function} function(chunk) where chunk is the entire
 *   message, or just part of it.
 */
module.exports = function createOpcMessageBuffer({ onCompleteMessage }) {

  let messageParts;
  let entireMessageSize;


  function reset() {
    messageParts = [];
    entireMessageSize = 0;
  }

  reset();

  // complete or parital chunk
  return (dataChunk) => {

    const json = dataChunk.toJSON();

    /* 1. add the dataChunk to the messageParts */

    // this is the start of a message
    if (messageParts.length === 0){

      // http://openpixelcontrol.org/
      const [ channel, command, lengthHigh, lengthLow ] = json.data;
      const dataSize = lengthHigh * 256 + lengthLow;
      entireMessageSize = dataSize + 4; // opcData + channel, command, lengthHigh, lengthLow

      messageParts = json.data;
    }
    // we already have some of the message, add this part to the
    else {
      messageParts = messageParts.concat(json.data);
    }

    /* 2. check to see if we have a full message */

    // if this chunk is all of the data, send it along
    if (entireMessageSize === messageParts.length){
      // console.log("full message, w00t!", messageParts.length);
      onCompleteMessage(messageParts);
      reset();
    }
    else if (messageParts.length > entireMessageSize){
      // console.log("something is fucked, resetting");
      reset();
    } else {
      // console.log("we have a partial message!", data.length);
    }

  };


};
