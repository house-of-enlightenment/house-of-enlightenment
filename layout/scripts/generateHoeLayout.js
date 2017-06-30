const R = require("ramda");
const { PI: π, sin, cos } = Math;
const Papa = require("papaparse");


/**
 *
 * @param {Array} data javascript array of { X, Y }
 * @return
 */
const generateLayout = exports.generateLayout = function generateLayout(data) {

  // doug's calculations have 92 pixels on the upper strip, 126 on the bottom
  // the order also doesn't match how the beagle bone's will be hooked up.
  // We need the top strip to have 90 pixels,
  // and we need the bottom string to be ordered top > bottom intead of bottom > top

  // the x/y coordinates for all 216 LEDs in a strip
  // at 0 radians (z will be 0)
  const slice = R.compose(

    ([ top, bottom ]) => {

      // in real life, the top strip will have 90 leds
      const newTop = R.take(90, top);

      // top > bottom
      const newBottom = R.reverse(bottom);

      return R.concat(newTop, newBottom);
    },

    // split the top and bottom strips
    R.splitAt(92),

    R.map(R.map(Number)) // for each point, then for X/Y, convert to Number
    // R.map(R.pick(["X", "Y"])) // we just need X and Y
  )(data);

  // 66 strips going around the center
  const strips = R.compose(

    R.flatten,

    R.map(i => {
      const angle = (i/66) * 2*π;

      const points = calculateSlicePoints(slice, angle);

      return R.map((xyz) => {
        return { point: R.values(xyz) };
      }, points);

    })

  )(R.range(0, 66));


  return strips;

};



function calculateSlicePoints(slice, angle) {

  // for each point in the slice
  return R.map(point => {

    const radius = point.X;

    const xyz = {
      x: cos(angle) * radius,
      y: point.Y,
      z: sin(angle) * radius
    };

    return xyz;

  })(slice);
}




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
