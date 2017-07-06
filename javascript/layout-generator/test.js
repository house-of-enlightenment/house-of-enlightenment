// this file should be used in a browser
import { generateLayoutFromCsvString } from "./generateHoeLayout.js";
import multiplySpire from "./multiplySpire.js";


fetch("/layout/spire.json")
  .then(res => res.json())
  .then(multiplySpire);


// load in data
fetch("/layout/files/led-coordinates.csv")
  .then(res => res.text())
  .then(csvString => {

    return generateLayoutFromCsvString(csvString)
      .then(data => {
        // console.log(data);
      });

  })
  .catch(error => {
    console.error("error reading led csv!", error);
  });
