// this file should be used in a browser

import { generateLayoutFromCsvString } from "./generateLayout.js";
import Papa from "papaparse";




// load in data
fetch("/layout/led-coordinates.csv")
  .then(res => res.text())
  .then(csvString => {

    return generateLayoutFromCsvString(csvString)
      .then(data => {
        console.log(data);
      });

  })
  .catch(error => {
    console.error("error reading led csv!", error);
  });
