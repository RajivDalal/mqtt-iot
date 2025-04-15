#include <Wire.h>
#include <LiquidCrystal_I2C.h>

#include <ESP8266WiFi.h>
#include <PubSubClient.h>

#define BLYNK_TEMPLATE_ID "TMPL3sa6ancZF"
#define BLYNK_TEMPLATE_NAME "CurrVolt"
#define BLYNK_AUTH_TOKEN "9u_h8DPGJEnyR024SFtrQ8lzjIz_J0TB"
#include <BlynkSimpleEsp8266.h>

BlynkTimer timer; 

char auth[] = BLYNK_AUTH_TOKEN;
const char * ssid = "Rajiv";
const char * pswrd = "Rajiv1234";
const char * mqtt_server = "192.168.154.37";

float voltage;
float current;

// #define TRIG_PIN D5  // GPIO14
// #define ECHO_PIN D6  // GPIO12

// #define VOLT_PIN D4
// #define LIGHT_PIN D5

WiFiClient espClient;
PubSubClient client(espClient);
LiquidCrystal_I2C lcd(0x27, 16, 2);

void setup_wifi()
{
  delay(100);
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print("Connecting to ");
  lcd.setCursor(0,1);
  lcd.print(ssid);

  WiFi.begin(ssid, pswrd);

  while (WiFi.status() != WL_CONNECTED){
    delay(500);
    lcd.print(".");
  }
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print("WiFi connected");
  delay(2000);
}

void reconnect(){
  // Loop until we're reconnected
  while(!client.connected()){
    lcd.clear();
    lcd.setCursor(0,0);
    lcd.print("Attempting MQTT");
    lcd.setCursor(0,1);
    lcd.print("connection...");
    delay(2000);
    // Attempt to connect
    if(client.connect("ESP8266Client")){
      lcd.clear();
      lcd.setCursor(0,0);
      lcd.print("MQTT Connected");
      // suscribe to the topic from the broker
      client.subscribe("esp/cmd");
      delay(2000);
    } else {
      lcd.setCursor(0,0);
      lcd.print("MQTT Failed");
      lcd.clear();
      lcd.setCursor(0,0); 
      lcd.print("Trying again in 5 seconds");
      delay(5000); // try to reconnect in 5 seconds
    }
  }
}

void callback(char * topic, byte * payload, unsigned int length){
  // Serial.print("Message arrived on topic: ");
  // Serial.print(topic);
  // Serial.print(". Message: ");
  String message;
  for(int i=0; i < length; i++){
    message += (char)payload[i];
  }
  Serial.println(message);

  // Handle the received messages
  if (String(topic) == "esp/cmd")
  {
    Serial.println("Received message: " + message);
    // Add code here to handle specific commands
    parseStr(message);
  }
}


void parseStr(const String& str) {
  // Find the position of the comma
  int commaIndex = str.indexOf(',');

  // Extract the text and state parts
  String sensorName = str.substring(0, commaIndex);
  int pinState = str.substring(commaIndex + 1).toInt();
  Serial.println("ApplianceName-> " + sensorName + ", State-> " + pinState);
}

void myTimer() 
{
  Blynk.virtualWrite(V0, current);
  Blynk.virtualWrite(V1, voltage);  
}

void setup() {
  Serial.begin(115200);
  delay(2000);

  Blynk.begin(auth,ssid,pswrd);
  timer.setInterval(1000L, myTimer); 


  lcd.init(); 
  lcd.backlight();
  lcd.clear();

  lcd.setCursor(0, 0);
  lcd.print("IoT Project");
  delay(1000);

  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);

  // pinMode(VOLT_PIN, OUTPUT);
  // pinMode(LIGHT_PIN, OUTPUT);

  // pinMode(TRIG_PIN, OUTPUT);
  // pinMode(ECHO_PIN, INPUT);
}

void loop() {

  if(!client.connected()){
    reconnect();
  }
  client.loop();

// ## DISTANCE ##
  // long duration;
  // float distance;

  // digitalWrite(TRIG_PIN, LOW);
  // delayMicroseconds(2);

  // digitalWrite(TRIG_PIN, HIGH);
  // delayMicroseconds(10);
  // digitalWrite(TRIG_PIN, LOW);

  // duration = pulseIn(ECHO_PIN, HIGH);
  // distance = duration * 0.0343 / 2;

  // lcd.setCursor(0, 0);
  // lcd.print("DISTANCE");
  // lcd.setCursor(0,1);
  // lcd.print(distance);
  // lcd.print(" cm");

  // delay(1000);
  // lcd.clear();
  

  int raw = analogRead(A0);
  voltage = (raw / 1023.0) * 3.3 * 5;
  current = (voltage - 2.5) / 0.185;

  Blynk.run();
  timer.run();

  Serial.println(raw);

  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print("Voltage:");
  lcd.setCursor(0,1);
  lcd.print(voltage);
  lcd.print(" V");
  delay(1000);
  
  lcd.clear();
  lcd.setCursor(0,0);
  lcd.print("Current:");
  lcd.setCursor(0,1);
  lcd.print(current);
  lcd.print(" A");
  delay(1000);

  String payload = String(current) + "," + String(voltage);

  client.publish("home/sensors/data", payload.c_str());
  Serial.print("Sensor data sent: ");
  Serial.println(payload);

  // lcd.clear();
  // lcd.setCursor(0,0);
  // lcd.print("Publishing.");
  // delay(500);
  // lcd.print(".");
  // delay(500);
  // lcd.print(".");
  // delay(2000); // Publish every 5 seconds

  // delay(3000);
  // int lightValue = analogRead(A0);
  // lcd.clear();
  // lcd.setCursor(0,0);
  // lcd.print("Light Lvl: ");
  // lcd.print(lightValue);
  // lcd.setCursor(0,1);
  // if(lightValue > 100)
  // {
  //   lcd.print("Day");
  // }
  // else
  // {
  //   lcd.print("Night");
  // }
  // digitalWrite(LIGHT_PIN, LOW);

}
