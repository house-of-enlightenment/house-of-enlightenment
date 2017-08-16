const R = require("ramda");
const { PI: π, sin, cos } = Math;
const Papa = require("papaparse");
const mapIndexed = R.addIndex(R.map);


/**
 * Transform data into hoeLayout format
 * This file can be used by node to generate and write a file
 * or used in a browser to ease development (see /test/)
 * @param {Array} data javascript array of { X, Y }
 * @return see readme.md in /layout/readme.md
 */
const generateLayout = exports.generateLayout = function generateLayout(data) {

  // doug's calculations have 92 pixels on the upper strip, 126 on the bottom
  // the order also doesn't match how the beagle bone's will be hooked up.
  // We need the top strip to have 90 pixels,
  // and we need the bottom string to be ordered top > bottom intead of bottom > top


  // the x/y coordinates for all 216 LEDs in the top/bottom strips
  // at 0 radians (z will be 0)
  const sliceAt0 = R.compose(

    ([ top, bottom ]) => {

      // in real life, the top strip will have 90 leds
      const newTop = R.take(90, top);

      // the order in the csv is bottom > top
      // we want top > bottom
      const newBottom = R.reverse(bottom);

      return { top: newTop, bottom: newBottom };
    },

    // split the top and bottom strips
    R.splitAt(92),

    R.map(R.map(Number)) // for each point, then for X/Y, convert to Number

    // R.map(R.pick(["X", "Y"])) // we just need X and Y
  )(data);


  // 66 strips going around the center
  const strips = R.compose(

    R.flatten,

    R.map(processSlice(sliceAt0))

  )(R.range(0, 66));

  // const maxMins = getMaxMins(strips);
  // console.log("maxMins", JSON.stringify(maxMins, null, 2));

  return strips;
};


function getMaxMins(strips){

  function maxMins(lookup, { point }) {

    // for each x, y, z
    return R.compose(
      R.map(
        i => ({
          min: R.min(point[i], R.path([i, "min"], lookup)),
          max: R.max(point[i], R.path([i, "max"], lookup))
        })
      )
    )(R.range(0, 3));

  }

  return R.reduce(maxMins, null, strips);

}

/**
 * @param sliceAt0 {Object} { top: [], bottom: [] }
 * @param sliceIndex {Number} 0 - 65
 * @return {Array} [{ point: {}, topOrBottom: "top" }, ... ]
 */
const processSlice = R.curry((sliceAt0, sliceIndex) => {

  const angle = (sliceIndex/66) * 2*π;

  // point { X, Y } (from csv)
  const calculateXYZ = point => {
    const radius = point.X;
    return  {
      x: cos(angle) * radius,
      y: point.Y,
      z: sin(angle) * radius
    };
  };

  /**
   * https://github.com/house-of-enlightenment/house-of-enlightenment/issues/5
   * @param  {Number} strip the strip id (0 - 131)
   * @return {String} the address
   */
  const getAddress = (strip) => {

    if (strip < 36){
      return "10.0.0.32";
    }
    else if (strip < 72){
      return "10.0.0.33";
    }
    else if (strip < 108) {
      return "10.0.0.34";
    }
    else {
      return "10.0.0.35";
    }
    
  };


  // for each strip top/bottom
  const topAndBottomPoints = R.mapObjIndexed(
    (strip, topOrBottom) => {

      // for each point in the strip
      return mapIndexed((point, i) => {

        // figure out the row (top > bottom). 0 based
        const row = (topOrBottom === "top")
          ? i + 126
          : 125 - i;

        const strip = topOrBottom === "top" ? sliceIndex * 2 : sliceIndex * 2 + 1;

        const address = getAddress(strip);

        const section = Math.floor(sliceIndex / 11);

        return {
          address,
          angle,
          point: R.values(calculateXYZ(point)),
          row,
          section,
          slice: sliceIndex,
          strip,
          stripIndex: i,
          topOrBottom
        };
      })(strip);
    }
  )(sliceAt0);

  // merge top/bottom together
  return R.compose(
    R.flatten,
    R.values
  )(topAndBottomPoints);
});





exports.generateLayoutFromCsvString = function(csvString) {

  return new Promise((resolve, reject) => {

    // parse the csv
    Papa.parse(csvString, {
      header: true,
      skipEmptyLines: true,
      complete: (response) => {

        const { data, errors, meta } = response;

        // console.log(response);

        if (errors.length > 0){
          reject(response);
        }
        else {
          resolve(generateLayout(data));
        }
      }
    });
  });
};
