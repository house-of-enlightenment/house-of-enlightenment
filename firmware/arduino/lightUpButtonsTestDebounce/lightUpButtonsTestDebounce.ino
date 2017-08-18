
//mapped to final boards
// Yellow, Green, White, Red, Blue
byte inPins[5] = {6, 5, 4, A3, A2};
byte outPins[5] = {7, 8,9, A0, A1 };

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
  lightUpButtons();

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
        if (buttonState[i] == LOW) {
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

void lightUpButtons() {

  for (int i = 0; i < 5; i++) {
    int sensorVal = digitalRead(inPins[i]);
    if (sensorVal == HIGH) {
      
      digitalWrite(outPins[i], LOW);
    } else {
      Serial.print("lighting pin:");
      Serial.println(i);
      digitalWrite(outPins[i], HIGH);
    }
  }
}

