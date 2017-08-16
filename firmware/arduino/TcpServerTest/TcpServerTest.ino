
#include <UIPEthernet.h>

EthernetServer server = EthernetServer(1000);

byte outPins[5] = {9, 7, A1 , 8, A0};
boolean outputLightState[5] = {0, 0, 0, 0, 0};

void setup()
{
  Serial.begin(9600);

  uint8_t mac[6] = {0x00, 0x01, 0x02, 0x03, 0x04, 0x05};
  IPAddress myIP(10, 0, 0, 55);

  Ethernet.begin(mac, myIP);

  server.begin();

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
  receiveMessage();
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
      Serial.write(msg, size);
      free(msg);
     updateLights();

    }
    Serial.println("");
    //client.println("DATA from Server!");
    //client.stop();
  }
}

//process the incoming message, store the new values in the lightstates and updat the outputs
void processMessage(char* msg, int size) {
  String s;
  for (int i = 0; i < size; i++) {
    Serial.write(msg[i]);
    if (msg[i] == '0'){
      Serial.println("writing 0");
      outputLightState[i] = false;
    }
    else{
      Serial.println("writing 1");
       outputLightState[i] = true;
    }
    s += msg[i];
  }
  Serial.print("i is: ");
  Serial.println(s);

}

void updateLights() {
  for (int i = 0; i <5; i++) {
    digitalWrite(outPins[i], outputLightState[i]);
  }
}

