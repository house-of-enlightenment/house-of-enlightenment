
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

byte mac[] = {
  0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED
}; // you can find this written on the board of some Arduino Ethernets or shields

void setup() {
  Ethernet.begin(mac, ip);
  Udp.begin(8888);

}


void loop() {
  //the message wants an OSC address as first argument
  OSCMessage msg("/analog/0");

  int sliderVal = analogRead(A1);

  sliderVal = map(sliderVal, 0, 1023, 0, 100);

  msg.add((int32_t)sliderVal);

  Udp.beginPacket(outIp, outPort);
  msg.send(Udp); // send the bytes to the SLIP stream
  Udp.endPacket(); // mark the end of the OSC Packet
  msg.empty(); // free space occupied by message

  delay(20);
}
