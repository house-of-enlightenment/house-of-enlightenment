// this file should be used in a browser

import { generateLayoutFromCsvString } from "./generateLayout.js";
import Papa from "papaparse";




// load in data
fetch("/layout/led-coordinates.csv")
  .then(res => res.text())
  .then(csvString => {

    generateLayoutFromCsvString(csvString)
      .then(data => {
        console.log(data);
      });

  });
