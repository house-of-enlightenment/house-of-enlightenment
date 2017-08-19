
#include <OSCMessage.h>
#include <UIPEthernet.h>
#include <UIPUdp.h>
#include <SPI.h>


EthernetUDP Udp;

//the Arduino's IP
//const byte stationId = 0;
//IPAddress ip(10, 0, 0, 55);
//byte mac[] = {
//  0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED
//}

const byte stationId = 1;
IPAddress ip(10, 0, 0, 56);
byte mac[] = {
  0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xEE
};

//const byte stationId = 2;
//IPAddress ip(10, 0, 0, 57);
//byte mac[] = {
//  0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED
//};

//const byte stationId = 3;
//IPAddress ip(10, 0, 0, 58);
//byte mac[] = {
//  0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED
//};

//const byte stationId = 4;
//IPAddress ip(10, 0, 0, 59);
//byte mac[] = {
//  0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED
//};

//const byte stationId = 5;
//IPAddress ip(10, 0, 0, 60);
//byte mac[] = {
//  0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED
//};

//destination IP
IPAddress outIp(10, 0, 0, 1);
const unsigned int outPort = 7000;
const unsigned int inPort = 9000;



EthernetServer server = EthernetServer(inPort);

//byte mac[] = {
//  0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED
//}; // you can find this written on the board of some Arduino Ethernets or shields

//mapped to test console
const unsigned int nButtons = 5;
const unsigned int nSliders = 1;
byte inPins[nButtons] = {6, 5, 4, A3, A2};
byte outPins[nButtons] = {7, 8, 9, A0, A1 };
const byte sliderIn[nSliders] = {A6};

int sliderVals[nSliders] = {0};
int oldSliderVals[nSliders] = {0};
int sliderLowVal = 10;
int sliderHighVal = 1013;

boolean buttonState[nButtons] = {0, 0, 0, 0, 0};
boolean lastButtonState[nButtons] = {0, 0, 0, 0, 0};
boolean ledState[nButtons] = {0, 0, 0, 0, 0};

unsigned long lastDebounceTime[] = {0, 0, 0, 0, 0};
unsigned long debounceDelay = 50;

unsigned long lastSliderReadTime = 0;

boolean outputLightState[nButtons] = {0, 0, 0, 0, 0};

// Keep track of which button state needs updated next
// As messages come in from ethernet, this gets updated
int outputLightStateIdx = 0;

void setup() {
  Ethernet.begin(mac, ip);
  Udp.begin(inPort);

  Serial.begin(9600);
  server.begin();
  //set up inputs
  for (int i = 0; i < nButtons; i++) {
    pinMode(inPins[i], INPUT_PULLUP);
  }

  //setup outputs
  for (int i = 0; i < nButtons; i++) {
    pinMode(outPins[i], OUTPUT);
  }
  for (int i = 0; i < nButtons; i++) {
    digitalWrite(outPins[i], LOW);
  }
  //  for (int i = 0; i < nSliders; i++) {
  //    pinMode(sliderIn[i], INPUT);
  //  }

}


void loop() {
  checkInputs();
  // readSliders();
  receiveMessage();
}

void buttonPress(int i) {
  OSCMessage msg("/input/button");
  //Serial.print(i);
  msg.add((int32_t)stationId);
  msg.add((int32_t)i);
  Udp.beginPacket(outIp, outPort);
  msg.send(Udp); // send the bytes to the SLIP stream
  Udp.endPacket(); // mark the end of the OSC Packet
  msg.empty(); // free space occupied by message
  //delay(20);
}

void sensorTouched(int sliderVal) {
  OSCMessage msg("/input/fader");
  msg.add((int32_t)stationId);
  msg.add((int32_t)sliderVal);
  Udp.beginPacket(outIp, outPort);
  msg.send(Udp); // send the bytes to the SLIP stream
  Udp.endPacket(); // mark the end of the OSC Packet
  msg.empty(); // free space occupied by message
  // delay(20);
}

void checkInputs() {
  for (int i = 0; i < nButtons; i++) {
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
          //          Serial.print("Buttoon ");
          //          Serial.print(i);
          //          Serial.println(" was pressed");
          buttonPress(i);
        }
      }
    }
    lastButtonState[i] = reading;
  }
}

//
//void printStates() {
//  for (int i = 0; i < nButtons; i++) {
//    int sensorVal = digitalRead(inPins[i]);
//    Serial.print(" Button ");
//    Serial.print(i);
//    Serial.print(" is ");
//    Serial.print(digitalRead(sensorVal));
//    if (sensorVal == HIGH) {
//      digitalWrite(outPins[i], LOW);
//    } else {
//      digitalWrite(outPins[i], HIGH);
//    }
//  }
//  Serial.println(" ");
//}

void lightUpButtons() {
  for (int i = 0; i < nButtons; i++) {
    int sensorVal = digitalRead(inPins[i]);
    if (sensorVal == HIGH) {
      digitalWrite(outPins[i], LOW);
    } else {
      digitalWrite(outPins[i], HIGH);
    }
  }
}

void readSliders() {
  if (millis() - lastSliderReadTime < debounceDelay) {
    return;
  }
  for (int i = 0; i < nSliders; i++) {
    int sliderVal = analogRead(sliderIn[i]);
    if ( sliderVal >= sliderLowVal && sliderVal <= sliderHighVal) {
      sliderVals[i] = map(sliderVal, sliderLowVal, sliderHighVal, 0, 100);
    }
    if (oldSliderVals[i] != sliderVals[i]) {
      oldSliderVals[i] = sliderVals[i];
      sensorTouched(sliderVals[i]);
      //      Serial.print("Slider");
      //      Serial.print(i);
      //      Serial.print(" is ");
      //      Serial.print(sliderVals[i]);
      //      Serial.print(" actual val is ");
      //      Serial.println(sliderVal);
    }
  }
  lastSliderReadTime = millis();
}


void receiveMessage() {
  size_t size;

  if (EthernetClient client = server.available())
  {
    while ((size = client.available()) > 0)
    {
      char* msg = (char*)malloc(size);
      size = client.read(msg, size);
      processMessage(msg, size);
      //Serial.write(msg, size);
      free(msg);
    }
    // Serial.println("");
    //client.println("DATA from Server!");
    //client.stop();
  }
}

void processMessage(char* msg, int size) {
  //String s;
  for (int i = 0; i < size; i++) {
    //Serial.write(msg[i]);
    if (msg[i] == '0') {
      //Serial.println("writing 0");
      outputLightState[outputLightStateIdx] = false;
    }
    else {
      //Serial.println("writing 1");
      outputLightState[outputLightStateIdx] = true;
    }
    outputLightStateIdx++;
    // If we've gotten an update for each button
    // reset and go make an update.
    if (outputLightStateIdx >= nButtons) {
      outputLightStateIdx = 0;
      updateLights();
    }
    //s += buttonStateMessage[i];
  }
  //Serial.print("i is: ");
  //Serial.println(s);
}


void updateLights() {
  for (int i = 0; i < nButtons; i++) {
    digitalWrite(outPins[i], outputLightState[i]);
  }
}
