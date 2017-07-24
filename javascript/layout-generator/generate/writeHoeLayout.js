const fs = require("fs");
const path = require("path");
const { generateLayoutFromCsvString } = require("./generateHoeLayout.js");
const multiplySpire = require("./multiplySpire.js");

/**
 * Usage: $ node nodeGenerateLayout.js
 * will generate and write write hoeLayout.json
 */

const layout = path.resolve(__dirname, "../../../layout")

fs.readFile(`${layout}/files/led-coordinates.csv`, "utf8", (err, csvString) => {

  if (err) throw err;

  generateLayoutFromCsvString(csvString)
    .then(data => {
      const json = JSON.stringify(data, null, 2);

      const destFile = path.resolve(`${layout}/hoeLayout.json`);

      fs.writeFile(destFile, json, (err) => {
        if (err) { throw err; }
        console.log(`${destFile} has been saved!`);
      });
    });

});

fs.readFile(`${layout}/files/spire.json`, "utf8", (err, data) => {
  if (err) throw err;

  const json = JSON.parse(data);

  const output = JSON.stringify(multiplySpire(json));

  const destFile = path.resolve(`${layout}/spire-large.json`);

  fs.writeFile(destFile, output, (err) => {
    if (err) { throw err; }
    console.log(`${destFile} has been saved!`);
  });
});
