const fs = require("fs");
const { generateLayoutFromCsvString } = require("./generateLayout.js");
const Papa = require("papaparse");

/**
 * Usage: $ node nodeGenerateLayout.js
 */

fs.readFile("./led-coordinates.csv", "utf8", (err, csvString) => {

  if (err) throw err;

  generateLayoutFromCsvString(csvString)
    .then(data => {
      const json = JSON.stringify(data, null, 2);

      fs.writeFile("layout.json", json, (err) => {
        if (err) { throw err; }
        console.log("layout.json has been saved!");
      });
    });

});
