
#include <OSCMessage.h>
#include <UIPEthernet.h>
#include <Udp.h>
#include <SPI.h>


EthernetUDP Udp;

//the Arduino's IP
IPAddress ip(10, 0, 0, 55);
//destination IP
IPAddress outIp(10, 0, 0, 30);
const unsigned int outPort = 7000;

//mapped to test console
int inPins[5] = {2, 4, 6, 5, 3};
byte outPins[5] = {9, 7, A1 , 8, A0};

int buttonState[5] = {0, 0, 0, 0, 0};
int lastButtonState[5] = {0, 0, 0, 0, 0};
int ledState[5] = {0, 0, 0, 0, 0};

unsigned long lastDebounceTime[] = {0, 0, 0, 0, 0};
unsigned long debounceDelay = 50;


byte mac[] = {
  0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED
}; // you can find this written on the board of some Arduino Ethernets or shields

void setup() {
  Ethernet.begin(mac, ip);
  Udp.begin(8888);

  Serial.begin(9600);
  //configure pin 2 as an input and enable the internal pull-up resistor

  //set up ijnputs
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
  //the message wants an OSC address as first argument
  //  OSCMessage msg("/analog/0");
  //  int sliderVal = analogRead(A1);
  //  sliderVal = map(sliderVal, 0, 1023, 0, 100);
  //  msg.add((int32_t)sliderVal);
  //  Udp.beginPacket(outIp, outPort);
  //  msg.send(Udp); // send the bytes to the SLIP stream
  //  Udp.endPacket(); // mark the end of the OSC Packet
  //  msg.empty(); // free space occupied by message

  //  int sensorVal = digitalRead(2);
  //  OSCMessage msg2("/button/0");
  //  msg2.add((int32_t)sensorVal);
  //  Udp.beginPacket(outIp, outPort);
  //  msg2.send(Udp); // send the bytes to the SLIP stream
  //  Udp.endPacket(); // mark the end of the OSC Packet
  //  msg2.empty(); // free space occupied by message

  //  if (digitalRead(2) == 0) {
  //    buttonPress();
  //  }

  checkInputs();
  lightUpButtons();


//  int sliderVal = analogRead(A1);
//  sliderVal = map(sliderVal, 0, 1023, 0, 100);
//  if (sliderVal != 0) {
//    sensorTouched(sliderVal);
//  }

//  delay(20);
}

//simulates a button press from station 0 button 1
void buttonPress(int i) {
  OSCMessage msg("/input/button");
  msg.add((int32_t)1);
  msg.add((int32_t)i);
  Udp.beginPacket(outIp, outPort);
  msg.send(Udp); // send the bytes to the SLIP stream
  Udp.endPacket(); // mark the end of the OSC Packet
  msg.empty(); // free space occupied by message

}

//void buttonPress() {
//  int sensorVal = digitalRead(2);
//  OSCMessage msg2("/button/0");
//  msg2.add((int32_t)sensorVal);
//  Udp.beginPacket(outIp, outPort);
//  msg2.send(Udp); // send the bytes to the SLIP stream
//  Udp.endPacket(); // mark the end of the OSC Packet
//  msg2.empty(); // free space occupied by message
//
//}

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
