//Using these softpots with a 10k pulldown https://learn.sparkfun.com/tutorials/softpot-hookup-guide

const int SOFT_POT_PIN1 = A6; // Pin connected to softpot wiper
const int SOFT_POT_PIN2 = A7; // Pin connected to softpot wiper

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
