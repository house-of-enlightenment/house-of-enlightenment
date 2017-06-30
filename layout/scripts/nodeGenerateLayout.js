const fs = require("fs");
const path = require("path");
const { generateLayoutFromCsvString } = require("./generateHoeLayout.js");
const multiplySpire = require("./multiplySpire.js");

/**
 * Usage: $ node nodeGenerateLayout.js
 */

fs.readFile("../files/led-coordinates.csv", "utf8", (err, csvString) => {

  if (err) throw err;

  generateLayoutFromCsvString(csvString)
    .then(data => {
      const json = JSON.stringify(data, null, 2);

      const destFile = path.resolve(__dirname, "../hoeLayout.json");

      fs.writeFile(destFile, json, (err) => {
        if (err) { throw err; }
        console.log("hoeLayout.json has been saved!");
      });
    });

});

fs.readFile("../files/spire.json", "utf8", (err, data) => {
  if (err) throw err;

  const json = JSON.parse(data);

  const output = JSON.stringify(multiplySpire(json));

  const destFile = path.resolve(__dirname, "../spire-large.json");

  fs.writeFile(destFile, output, (err) => {
    if (err) { throw err; }
    console.log("spire-large.json has been saved!")
  });
});
