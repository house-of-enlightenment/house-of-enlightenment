const fs = require("fs");
const { generateLayoutFromCsvString } = require("./generateHoeLayout.js");
const multiplySpire = require("./multiplySpire.js");


/**
 * Usage: $ node nodeGenerateLayout.js
 */

fs.readFile("./led-coordinates.csv", "utf8", (err, csvString) => {

  if (err) throw err;

  generateLayoutFromCsvString(csvString)
    .then(data => {
      const json = JSON.stringify(data, null, 2);

      fs.writeFile("hoeLayout.json", json, (err) => {
        if (err) { throw err; }
        console.log("hoeLayout.json has been saved!");
      });
    });

});

// fs.readFile("./spire.json", "utf8", (err, data) => {
//   if (err) throw err;
//
//   const json = JSON.parse(data);
//
//   const output = JSON.stringify(multiplySpire(json));
//
//   fs.writeFile("spire-large.json", output, (err) => {
//     if (err) { throw err; }
//     console.log("spire-large.json has been saved!")
//   });
// });
