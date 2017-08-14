
#include <OSCMessage.h>
#include <UIPEthernet.h>
#include <UIPUdp.h>
#include <SPI.h>


EthernetUDP Udp;

//the Arduino's IP
IPAddress ip(10, 0, 0, 55);
//destination IP
IPAddress outIp(10, 0, 0, 30);
const unsigned int outPort = 7000;

byte mac[] = {
  0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED
}; // you can find this written on the board of some Arduino Ethernets or shields

//mapped to test console
int inPins[5] = {A2, 4, 6, 5, 3};
byte outPins[5] = {9, 7, A1 , 8, A0};

boolean buttonState[5] = {0, 0, 0, 0, 0};
boolean lastButtonState[5] = {0, 0, 0, 0, 0};
boolean ledState[5] = {0, 0, 0, 0, 0};

unsigned long lastDebounceTime[] = {0, 0, 0, 0, 0};
unsigned long debounceDelay = 50;



void setup() {
  Ethernet.begin(mac, ip);
  Udp.begin(8888);

  Serial.begin(9600);

  //set up inputs
  for (int i = 0; i < 5; i++) {
    pinMode(inPins[i], INPUT_PULLUP);
  }

  //setup outputs
  for (int i = 0; i < 5; i++) {
    pinMode(outPins[i], OUTPUT);
  }
  for (int i = 0; i < 5; i++) {
    digitalWrite(outPins[i], LOW);
  }

}


void loop() {
 // buttonPress(1);
  checkInputs();
  lightUpButtons();
}


void buttonPress(int i) {
  OSCMessage msg("/input/button");
  Serial.print(i);
  msg.add((int32_t)1);
  msg.add((int32_t)i);
  Udp.beginPacket(outIp, outPort);
  msg.send(Udp); // send the bytes to the SLIP stream
  Udp.endPacket(); // mark the end of the OSC Packet
  msg.empty(); // free space occupied by message
  delay(20);

}



//simulates a fader input from station 0 fader 1
void sensorTouched(int sliderVal) {
  OSCMessage msg("/input/fader");
  msg.add((int32_t)0);
  msg.add((int32_t)0);
  msg.add((int32_t)sliderVal);
  Udp.beginPacket(outIp, outPort);
  msg.send(Udp); // send the bytes to the SLIP stream
  Udp.endPacket(); // mark the end of the OSC Packet
  msg.empty(); // free space occupied by message
  delay(20);

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

          buttonPress(i);
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
      digitalWrite(outPins[i], HIGH);
    }
  }
}

