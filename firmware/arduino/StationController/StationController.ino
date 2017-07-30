#include <OSCMessage.h>
#include <UIPEthernet.h>
#include <UIPUdp.h>
#include <SPI.h>
#include <OSCMessage.h>

EthernetUDP Udp;

//the Arduino's IP
IPAddress ip(10, 0, 0, 55);
//destination IP
IPAddress outIp(10, 0, 0, 30);
const unsigned int outPort = 7000;

const int BUTTON_PIN = 2;

byte mac[] = {
  0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED
}; // you can find this written on the board of some Arduino Ethernets or shields
void setup() {
  Ethernet.begin(mac, ip);
  Udp.begin(8888);

  pinMode(BUTTON_PIN, INPUT_PULLUP);

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

  if (digitalRead(2) == 0) {
    buttonPress();
  }
  int sliderVal = analogRead(A1);
  sliderVal = map(sliderVal, 0, 1023, 0, 100);
  if (sliderVal != 0) {
    sensorTouched(sliderVal);
  }

  delay(20);
}

//simulates a button press from station 0 button 1
void buttonPress() {
  int sensorVal = digitalRead(2);
  OSCMessage msg2("/input/button");
  msg2.add((int32_t)0);
  msg2.add((int32_t)1);
  Udp.beginPacket(outIp, outPort);
  msg2.send(Udp); // send the bytes to the SLIP stream
  Udp.endPacket(); // mark the end of the OSC Packet
  msg2.empty(); // free space occupied by message

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

