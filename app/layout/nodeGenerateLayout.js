const fs = require("fs");
const generateLayout = require("./generateLayout.js");

/**
 * Usage: $ node nodeGenerateLayout.js
 */

fs.readFile("./lower-led-data.json", "utf8", (err, data) => {

  if (err) throw err;

  const points = JSON.stringify(generateLayout(JSON.parse(data)));

  fs.writeFile("lower-points.json", points, (err) => {
    if (err) { throw err; }
    console.log("The file has been saved!");
  });

});
