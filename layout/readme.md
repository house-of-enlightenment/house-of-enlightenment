
# hoeLayout.json
A json file that contains an array of 14,256 points.  (66 slices x 216 LEDs per slice). Each slice is broken into 2 strips of LEDs.  The top strip has 90 LEDs, the bottom strip has 126 LEDs.

Each point is an object shaped like this:
```
{
  address: "10.0.0.32",
  angle : 0,
  point : [ 0, 0, 0 ],
  row: 0,
  section: 0,
  slice: 0,
  strip: 0,
  stripIndex: 0,
  topOrBottom : "top"
}
```

#### address : `String`
`10.0.0.32` - first 48 strips  
`10.0.0.33` - next 48 strips  
`10.0.0.34` - final 36 strips  

#### angle : `Number`
(is this useful?)  
An angle from 0 to 2π.

#### point : `Array`
eg. `[ 0, 0, 0 ]`
x, y, z positions

The point in physical space in inches from the center on the ground.

#### row : `Number`
Index from 0-215. bottom > top.  
eg. the bottom pixel in a slice is 0, the top is 215.  This is independent of how the LEDs are wired.

#### section : `Number`
0-5.  Which of the 6 sections this LED is in.

#### slice : `Number`
0-65.  This is essentially the _column_.

#### strip : `Number`
0-131. The id of the strip connected to the beaglebone.

#### stripIndex : `Number`
(needs a better name?)  
The index of this LED relative to the strip.  0 is the first.
This will be 0-89 for the top LED strip and 0-125 for the bottom LED strip.

#### topOrBottom : `String`
(is this useful?)  
"top" or "bottom".  Which strip in this slice the LED belongs to.


## To generate hoeLayout.json
```
gulp layout
```

## To change hoeLayout.json
The file that generates `hoeLayout.json` is `/javascript/layout-generator/generateHoeLayout.js`
