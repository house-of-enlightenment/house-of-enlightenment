const fs = require("fs");
const generateLayout = require("./generateLayout.js");
const Papa = require("papaparse");

/**
 * Usage: $ node nodeGenerateLayout.js
 */

fs.readFile("./led-coordinates.csv", "utf8", (err, data) => {

  if (err) throw err;

  // parse the csv and generate layout.json
  Papa.parse(data, {
    header: true,
    skipEmptyLines: true,
    complete: (response) => {

      const { data, errors, meta } = response;

      // console.log(response);

      if (errors.length > 0){
        console.error(JSON.stringify(errors));
      }
      else {
        const json = JSON.stringify(generateLayout(data), null, 2);

        fs.writeFile("layout.json", json, (err) => {
          if (err) { throw err; }
          console.log("layout.json has been saved!");
        });

      }
    }
  });


});
