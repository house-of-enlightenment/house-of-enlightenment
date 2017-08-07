
#include <UIPEthernet.h>
#include <UIPUdp.h>
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


//converts the pin to an osc address
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

/**
   TONE

   square wave output "/tone"

   format:
   /tone/pin

     (digital value) (float value) = freqency in Hz
     (no value) disable tone

 **/
void routeTest(OSCMessage &msg) {
	Serial.println("received a test message");

}


void routeTone(OSCMessage &msg, int addrOffset ) {
  //iterate through all the analog pins
  Serial.println("received a message");
  //  for (int i = 0; i < 5; i++) {
  //
  //    digitalWrite(outPins[i], HIGH);
  //
  //  }

  //Serial.println(addrOffset);
  for (byte pin = 0; pin < NUM_DIGITAL_PINS; pin++) {
    //match against the pin number strings

    int pinMatched = msg.match(numToOSCAddress(pin), addrOffset);
    if (pinMatched) {
      Serial.print("pin is ");
      Serial.println(pin);
      unsigned int frequency = 0;
      //if it has an int, then it's an integers frequency in Hz
      if (msg.isInt(0)) {
        frequency = msg.getInt(0);
        Serial.print("frequency is ");
        Serial.println(frequency);
      } //otherwise it's a floating point frequency in Hz
      else if (msg.isFloat(0)) {
        frequency = msg.getFloat(0);
      }
      else
        noTone(pin);
      if (frequency > 0)
      {
        if (msg.isInt(1))
          tone(pin, frequency, msg.getInt(1));
        else
          tone(pin, frequency);
      }
    }
  }
}

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
//reads and dispatches the incoming message
void loop() {
  OSCMessage bundleIN;
  int size;
  int success;

  if ( (size = Udp.parsePacket()) > 0)
  {
    Serial.println("something in main loop");
    Serial.print("size is ");
    Serial.println(size);
    while (size--) {
      uint8_t b = Udp.read();
      bundleIN.fill(b);
      Serial.print("reading udp packet size is ");
      Serial.println(b);
    }

    if (!bundleIN.hasError()) {
      Serial.print("Routing now, bundle size is ");
      Serial.println(bundleIN.size());
      Serial.print("bundel has error?  ");
      Serial.println(bundleIN.hasError());

      //  OSCMessage msg = bundleIN.getOSCMessage(0);

	  Serial.print("routing the message, result is: ");
      //Serial.print(bundleIN.route("/tone", routeTone));
	  //Serial.print(" and ");
	  Serial.println(bundleIN.dispatch("/test", routeTest));

    }

    Udp.flush();
//    Udp.endPacket();
 //   Udp.stop();
    //    if (bundleIN.hasError())
    //      Serial.println("had an error");
  }
}


