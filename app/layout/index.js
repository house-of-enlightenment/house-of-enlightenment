// this file should be used in a browser

import generateLayout from "./generateLayout.js";

// load in data
fetch("layout/lower-led-data.json")
  .then(res => res.json())
  .then(data => {
    console.log(generateLayout(data));
  });
