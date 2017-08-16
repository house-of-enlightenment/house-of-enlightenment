#include <OSCMessage.h>
#include <UIPEthernet.h>

EthernetServer server = EthernetServer(1000);
EthernetUDP Udp;

int inPins[5] = {A2, 4, 6, 5, 3};
byte outPins[5] = {9, 7, A1 , 8, A0};
boolean outputLightState[5] = {0, 0, 0, 0, 0};

int buttonState[5] = {0, 0, 0, 0, 0};
int lastButtonState[5] = {0, 0, 0, 0, 0};
int ledState[5] = {0, 0, 0, 0, 0};

unsigned long lastDebounceTime[] = {0, 0, 0, 0, 0};
unsigned long debounceDelay = 50;

IPAddress outIp(10, 0, 0, 30);
const unsigned int outPort = 7000;

void setup()
{
  Serial.begin(9600);

  uint8_t mac[6] = {0x00, 0x01, 0x02, 0x03, 0x04, 0x05};
  IPAddress myIP(10, 0, 0, 55);

  Ethernet.begin(mac, myIP);
  Udp.begin(8888);

  server.begin();

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

void loop()
{
  // Serial.println("running");
  receiveMessage();
  checkInputs();
  //updateLights();
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
      //    Serial.write(msg, size);
      free(msg);
      updateLights();

    }
    //    Serial.println("");
    //client.println("DATA from Server!");
    //client.stop();
  }
}

//process the incoming message, store the new values in the lightstates and updat the outputs
void processMessage(char* msg, int size) {
  String s;
  for (int i = 0; i < size; i++) {
    //    Serial.write(msg[i]);
    if (msg[i] == '0') {
      //      Serial.println("writing 0");
      outputLightState[i] = false;
    }
    else {
      //     Serial.println("writing 1");
      outputLightState[i] = true;
    }
    s += msg[i];
  }
  //  Serial.print("i is: ");
  // Serial.println(s);

}

void updateLights() {
  for (int i = 0; i < 5; i++) {
    digitalWrite(outPins[i], outputLightState[i]);
  }
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

void buttonPress(int i) {
  OSCMessage msg("/input/button");
  Serial.print(i);
  msg.add((int32_t)1);
  msg.add((int32_t)i);
  Udp.beginPacket(outIp, outPort);
  msg.send(Udp); // send the bytes to the SLIP stream
  Udp.endPacket(); // mark the end of the OSC Packet
  msg.empty(); // free space occupied by message
  //delay(20);

}
