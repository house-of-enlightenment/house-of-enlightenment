const assert = require("assert");


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

  let headerPartsAvailable;
  let messageParts;
  let entireMessageSize;


  function handlePartialHeader(dataChunk) {
    const totalLength = dataChunk.length + headerPartsAvailable;
    const buffer = Buffer.concat([messageParts, dataChunk]);

    assert(totalLength == buffer.length, totalLength + " != " + buffer.length);

    if (totalLength >= 4) {
      // we have enough data to process normally now
      reset();
      parseNewChunk(buffer);
    } else {
      // not enough data yet. so just save this and hope some more
      // data comes in
      headerPartsAvailable = totalLength;
      messageParts = buffer;
    }
  }

  function parseNewChunk(dataChunk) {
    assert(messageParts.length == 0);
    // yeah, seriously, I saw a couple messages of length 3
    if (dataChunk.length < 4) {
      handlePartialHeader(dataChunk);
      return;
    }
    headerPartsAvailable = 4;

    const channel = dataChunk[0];
    const command = dataChunk[1];
    const lengthHigh = dataChunk[2];
    const lengthLow = dataChunk[3];
    const dataSize = lengthHigh * 256 + lengthLow;

    if (isNaN(dataSize)) {
      console.log("Got a NaN data size!");
      console.log(dataChunk);
    }

    if (dataSize + 4 == dataChunk.length) {
      // we have a full message.  just pass it along
      onCompleteMessage(dataChunk);
    } else {
      entireMessageSize = dataSize + 4; // (channel, command, lengthHigh, lengthLow) + opcData
      parseExistingChunk(dataChunk);
    }
  }

  function parseExistingChunk(dataChunk) {
    const remaining = entireMessageSize - messageParts.length;

    assert(
      remaining > 0,
      remaining + " remaining: " + entireMessageSize + " - " + messageParts.length
    );

    if (dataChunk.length < remaining) {
      messageParts = Buffer.concat([messageParts, dataChunk]);
    } else if (dataChunk.length == remaining) {
      const completeMessage = Buffer.concat([messageParts, dataChunk]);
      onCompleteMessage(completeMessage);
      reset();
    } else {
      const completeMessage = Buffer.concat([messageParts, dataChunk.slice(0, remaining)]);
      onCompleteMessage(completeMessage);
      reset();
      parseNewChunk(dataChunk.slice(remaining));
    }
  }

  function reset() {
    messageParts = Buffer.alloc(0);
    entireMessageSize = 0;
    headerPartsAvailable = 0;
  }

  reset();

  // complete or parital chunk
  return (dataChunk) => {

    // this is the start of a message
    if (messageParts.length == 0) {
      parseNewChunk(dataChunk);
    }
    // we already have some of the message, add the remainder / what we can
    else {
      if (headerPartsAvailable >= 4) {
        parseExistingChunk(dataChunk);
      } else {
        handlePartialHeader(dataChunk);
      }
    }
  };


};
