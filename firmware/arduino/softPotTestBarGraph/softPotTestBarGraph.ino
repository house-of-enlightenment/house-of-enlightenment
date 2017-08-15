/******************************************************************************
SoftPot_Example.ino
Example sketch for SparkFun's soft membrane potentiometer
  (https://www.sparkfun.com/products/8680)
Jim Lindblom @ SparkFun Electronics
April 28, 2016

- Connect the softpot's outside pins to 5V and GND (the outer pin with an arrow
indicator should be connected to GND). 
- Connect the middle pin to A0.

As the voltage output of the softpot changes, a line graph printed to the
serial monitor should match the wiper's position.

Development environment specifics:
Arduino 1.6.7
******************************************************************************/
const byte SOFT_POT_PIN1 = A6; // Pin connected to softpot wiper
const byte SOFT_POT_PIN2 = A7; // Pin connected to softpot wiper

const int GRAPH_LENGTH = 40; // Length of line graph

void setup() 
{
  Serial.begin(9600);
  pinMode(SOFT_POT_PIN1, INPUT);
  pinMode(SOFT_POT_PIN2, INPUT);
}

void loop() 
{
  // Read in the soft pot's ADC value
  int softPotADC1 = analogRead(SOFT_POT_PIN1);
  int softPotADC2 = analogRead(SOFT_POT_PIN2);
  // Map the 0-1023 value to 0-40
  int softPotPosition1 = map(softPotADC1, 0, 1023, 0, GRAPH_LENGTH);
  int softPotPosition2 = map(softPotADC2, 0, 1023, 0, GRAPH_LENGTH);

  // Print a line graph:
  Serial.print("<"); // Starting end
  for (int i=0; i<GRAPH_LENGTH; i++)
  {
    if (i == softPotPosition1) Serial.print("|");
    else Serial.print("-");
  }
  Serial.print("> (" + String(softPotADC1) + ") ");

  Serial.print("<"); // Starting end
  for (int i=0; i<GRAPH_LENGTH; i++)
  {
    if (i == softPotPosition2) Serial.print("|");
    else Serial.print("-");
  }
  Serial.println("> (" + String(softPotADC2) + ") ");

  delay(100);
}
