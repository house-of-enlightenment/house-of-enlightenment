const R = require("ramda");
const { PI: π, sin, cos } = Math;
const Papa = require("papaparse");


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
          reject(JSON.stringify(errors));
        }
        else {
          resolve(generateLayout(data));
        }
      }
    });
  });
};


/**
 *
 * @param {Object} data json data via
 *                      $ csvjson Lower\ LED\ Strip.csv > lower-led-data.json
 * @return
 */
const generateLayout = exports.generateLayout = function generateLayout(data) {

  // the x/y coordinates for all 127 LEDs in a strip
  // at 0 radians (z will be 0)
  const slice = R.compose(
    R.map(R.map(Number)), // for each point, then for x/y, convert to Number
    R.map(R.pick(["X", "Y"])),
    R.tail
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
