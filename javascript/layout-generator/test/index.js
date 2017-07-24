import { generateLayoutFromCsvString } from "../generate/generateHoeLayout.js";
import multiplySpire from "../generate/multiplySpire.js";

/* this file should be used in a browser */

fetch("/data/spire.json")
  .then(res => res.json())
  .then(multiplySpire);


// load in data
fetch("/data/led-coordinates.csv")
  .then(res => res.text())
  .then(csvString => {

    // generate the layout file and log to the console
    return generateLayoutFromCsvString(csvString)
      .then(data => {
        console.log(data); // eslint-disable-line no-console
      });

  })
  .catch(error => {
    console.error("error reading led csv!", error);
  });
