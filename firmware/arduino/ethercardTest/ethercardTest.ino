#include <EtherCard.h>

// Ethernet IP, default gateway and MAC addresses
static byte myip[] = { 10,0,0,55 };
static byte gwip[] = { 10,0,0,1 };
static byte mymac[] = { 0x74,0x69,0x69,0x2D,0x30,0x31 };

byte Ethernet::buffer[500]; // tcp/ip send and receive buffer

const char page[] PROGMEM =
"HTTP/1.0 503 Service Unavailable\r\n"
"Content-Type: text/html\r\n"
"Retry-After: 600\r\n"
"\r\n"
"<html>"
  "<head><title>"
    "Hello World!"
  "</title></head>"
  "<body>"
    "<h3>Hello World! This is your Arduino speaking!</h3>"
  "</body>"
"</html>";

int inPin = 2;
int val = 0;

void setup(){
  Serial.begin(57600);
  Serial.println("\n[Hello World]");

  pinMode(inPin, INPUT_PULLUP);

  if (ether.begin(sizeof Ethernet::buffer, mymac) == 0) 
    Serial.println( "Failed to access Ethernet controller");
  ether.staticSetup(myip, gwip);

  ether.printIp("IP:  ", ether.myip);
  ether.printIp("GW:  ", ether.gwip);  
  ether.printIp("DNS: ", ether.dnsip);  
}

void loop(){
    val = digitalRead(inPin);   // read the input pin
  
  // wait for an incoming TCP packet, but ignore its contents
  if (ether.packetLoop(ether.packetReceive())) {
    memcpy_P(ether.tcpOffset(), page, sizeof page);
    ether.httpServerReply(sizeof page - 1);
  }
  Serial.println(val);
}
