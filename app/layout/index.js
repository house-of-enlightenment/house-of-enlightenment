// this file should be used in a browser

import generateLayout from "./generateLayout.js";
import Papa from "papaparse";




// load in data
fetch("/layout/led-coordinates.csv")
  .then(res => res.text())
  .then(csvText => {

    // parse the csv
    Papa.parse(csvText, {
      header: true,
      skipEmptyLines: true,
      complete: (response) => {

        const { data, errors, meta } = response;

        // console.log(response);

        if (errors.length > 0){
          console.error(JSON.stringify(errors));
        }
        else {
          console.log(generateLayout(data));
        }
      }
    });

  });
