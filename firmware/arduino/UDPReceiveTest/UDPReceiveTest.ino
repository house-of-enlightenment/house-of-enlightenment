

#include <UIPEthernet.h>
#include <UIPUdp.h>
//#include <EthernetUdp.h>
#include <SPI.h>

#include <OSCBundle.h>
#include <OSCBoards.h>

/*
  UDPReceiveOSC
  Set a tone according to incoming OSC control
                            Adrian Freed
*/

//UDP communication


EthernetUDP Udp;
byte mac[] = {
  0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED
}; // you can find this written on the board of some Arduino Ethernets or shields

//the Arduino's IP
IPAddress ip(10, 0, 0, 55);

//port numbers
const unsigned int inPort = 9000;

byte outPins[5] = {9, 7, A1 , 8, A0};
boolean outputLightState[5] = {0, 0, 0, 0, 0};
boolean outputState = false;


//void routeTone(OSCMessage &msg, int addrOffset ) {
//  //iterate through all the analog pins
//  Serial.print(" in the main function ");
//  for (byte pin = 0; pin < NUM_DIGITAL_PINS; pin++) {
//    //match against the pin number strings
//    int pinMatched = msg.match(numToOSCAddress(pin), addrOffset);
//    if (pinMatched) {
//      unsigned int frequency = 0;
//      //if it has an int, then it's an integers frequency in Hz
//      if (msg.isInt(0)) {
//        frequency = msg.getInt(0);
//      } //otherwise it's a floating point frequency in Hz
//      else if (msg.isFloat(0)) {
//        frequency = msg.getFloat(0);
//      }
//      else
//        noTone(pin);
//      if (frequency > 0)
//      {
//        if (msg.isInt(1))
//          tone(pin, frequency, msg.getInt(1));
//        else
//          tone(pin, frequency);
//      }
//    }
//  }
//}



void setup() {
  //setup ethernet part
  Ethernet.begin(mac, ip);

  Udp.begin(inPort);
  Serial.begin(9600);

  //setup outputs
  for (int i = 0; i < 5; i++) {
    pinMode(outPins[i], OUTPUT);
  }
  for (int i = 0; i < 5; i++) {
    digitalWrite(outPins[i], LOW);
  }

}

char * numToOSCAddress( int pin) {
  static char s[10];
  int i = 9;

  s[i--] = '\0';
  do
  {
    s[i] = "0123456789"[pin % 10];
    --i;
    pin /= 10;
  }
  while (pin && i);
  s[i] = '/';
  return &s[i];
}
//reads and dispatches the incoming message
void loop() {

  OSCMsgReceive();

}


void OSCMsgReceive() {
  OSCMessage msgIN;
  int sizeOf;
  if ((sizeOf = Udp.parsePacket()) > 0) {
    Serial.println("Recxeived a packet");
    while (sizeOf--) {
      //Serial.print("size is: ");
      //Serial.println(sizeOf);
      msgIN.fill(Udp.read());
    }
    if (!msgIN.hasError()) {
      Serial.println("\na message received, routing now ");
      msgIN.route("/button/0", routeButton0);
      msgIN.route("/button/1", routeButton1);
      msgIN.route("/button/2", routeButton2);
      msgIN.route("/button/3", routeButton3);
      msgIN.route("/button/4", routeButton4);
      // msgIN.route("/Fader/Value",funcValue);
    }
    if (msgIN.hasError()) {
      Serial.println("    ----->>>>> Theres an error message");
    }
    Udp.flush();
    Udp.stop();
    Udp.begin(inPort);
  }
}

void routeButton0(OSCMessage &msg, int addrOffset ) {
  boolean ledState = (boolean) msg.getInt(0);
  Serial.print("got Button Message0: ");
  Serial.println(ledState);
  Serial.print("got Button Message offset : ");
  Serial.println(addrOffset);
  Serial.print("got address message : ");
  Serial.println(msg.getAddress(numToOSCAddress(0), addrOffset));
  toggleLights(0);
}

void routeButton1(OSCMessage &msg, int addrOffset ) {
  boolean ledState = (boolean) msg.getInt(0);
  Serial.print("got Button Message0: ");
  Serial.println(ledState);
  Serial.print("got Button Message offset : ");
  Serial.println(addrOffset);
  Serial.print("got address message : ");
  Serial.println(msg.getAddress(numToOSCAddress(1), addrOffset));
  toggleLights(1);
}
void routeButton2(OSCMessage &msg, int addrOffset ) {
  boolean ledState = (boolean) msg.getInt(0);
  Serial.print("got Button Message0: ");
  Serial.println(ledState);
  Serial.print("got Button Message offset : ");
  Serial.println(addrOffset);
  toggleLights(2);
}
void routeButton3(OSCMessage &msg, int addrOffset ) {
  boolean ledState = (boolean) msg.getInt(0);
  Serial.print("got Button Message0: ");
  Serial.println(ledState);
  Serial.print("got Button Message offset : ");
  Serial.println(addrOffset);
  toggleLights(3);
}
void routeButton4(OSCMessage &msg, int addrOffset ) {
  boolean ledState = (boolean) msg.getInt(0);
  Serial.print("got Button Message0: ");
  Serial.println(ledState);
  Serial.print("got Button Message offset : ");
  Serial.println(addrOffset);
  toggleLights(4);
}


void toggleLights(int val) {
  //outputState = !outputState;

  outputLightState[val] = !outputLightState[val];
  Serial.print("setting output state :");
  Serial.print(outputLightState[val]);
  Serial.print(" and ");
  Serial.println(val);
  //  for (int i = 0; i++; i < 5) {
  //    digitalWrite(outPins[i], outputState);
  //  }
  digitalWrite(outPins[val], outputLightState[val]);
  //  digitalWrite(outPins[1], outputState);
  //  digitalWrite(outPins[2], outputState);
  //  digitalWrite(outPins[3], outputState);
  //  digitalWrite(outPins[4], outputState);
}


//  OSCBundle bundleIN;
//  int size;
//
//  if ( (size = Udp.parsePacket()) > 0)
//  {
//    while (size--) {
//      bundleIN.fill(Udp.read());
//    }
//    if (!bundleIN.hasError()) {
//      Serial.println("Routing message: ");
//
//      //Serial.println(bundleIN.getOSCMessage(0).getDataLength(0));
////      bundleIN.dispatch("/tone", routeTone);
//      bundleIN.route("/tony", routeTony);
//    }
//  }
//  Udp.flush();
//  Udp.stop();
//  Udp.begin(inPort);
//
//  //  if (Udp.begin(inPort))
//  //    Serial.println("restart connection: succeeded%\r\n");
//  //  else
//  //    Serial.println("restart connection: failed%\r\n");
//
//}


