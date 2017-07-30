
//mapped to test console
int inPins[5] = {7, 4, 6, 5, 3};
int outPins[5] = {10, 8, 11 , 9, 12};

int buttonState[5] = {0, 0, 0, 0, 0};
int lastButtonState[5] = {0, 0, 0, 0, 0};
int ledState[5] = {0, 0, 0, 0, 0};

unsigned long lastDebounceTime[] = {0, 0, 0, 0, 0};
unsigned long debounceDelay = 50;

void setup() {
  //start serial connection
  Serial.begin(9600);
  //configure pin 2 as an input and enable the internal pull-up resistor

  for (int i = 0; i < 5; i++) {
    pinMode(inPins[i], INPUT_PULLUP);
  }

  for (int i = 0; i < 5; i++) {
    pinMode(outPins[i], OUTPUT);
  }
  for (int i = 0; i < 5; i++) {
    digitalWrite(outPins[i], LOW);
  }
}

void loop() {
  checkInputs();

}

void checkInputs() {
  for (int i = 0; i < 5; i++) {
    int reading = digitalRead(inPins[i]);

    if (reading != lastButtonState[i]) {
      // reset the debouncing timer
      lastDebounceTime[i] = millis();
    }
    if ((millis() - lastDebounceTime[i]) > debounceDelay) {
      if (reading != buttonState[i]) {
        buttonState[i] = reading;

        // only toggle the LED if the new button state is HIGH
        if (buttonState[i] == HIGH) {
          ledState[i] = !ledState[i];
          Serial.print("Buttoon ");
          Serial.print(i);
          Serial.println(" was pressed");
        }
      }
    }
    lastButtonState[i] = reading;
  }
}

void printStates() {

  for (int i = 0; i < 5; i++) {
    int sensorVal = digitalRead(inPins[i]);

    Serial.print(" Button ");
    Serial.print(i);
    Serial.print(" is ");
    Serial.print(digitalRead(sensorVal));

    if (sensorVal == HIGH) {
      digitalWrite(outPins[i], LOW);
    } else {
      digitalWrite(outPins[i], HIGH);
    }
  }
  Serial.println(" ");
}

