#include <WiFi.h>
#include <PubSubClient.h>
#include <ESP32Servo.h> // Include the Servo library
#include <LiquidCrystal_I2C.h>
const char* ssid = "Wokwi-GUEST";
const char* password = "";

const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;
const char* mqtt_username = "";
const char* mqtt_password = "";
const char* mqtt_topic = "solar_data";

LiquidCrystal_I2C LCD = LiquidCrystal_I2C(0x27, 16, 2);

WiFiClient espClient;
PubSubClient client(espClient);
Servo panServo;  // Create a Servo object for pan
Servo tiltServo; // Create a Servo object for tilt
const int builtInLedPin = 2;  // Define the GPIO pin for the built-in LED

void setup() {
  Serial.begin(115200);

  LCD.init();
  LCD.backlight();
  LCD.setCursor(0, 0);
  LCD.print("Connecting to ");
  LCD.setCursor(0, 1);
  LCD.print("WiFi ");

  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
  panServo.attach(18); // Attach pan servo to GPIO 18 on ESP32
  tiltServo.attach(19); // Attach tilt servo to GPIO 19 on ESP32
  pinMode(builtInLedPin, OUTPUT);  // Set the built-in LED pin as an output
  digitalWrite(builtInLedPin, LOW);  // Turn off the built-in LED initially

  reconnect();
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
}

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    LCD.clear();
    LCD.setCursor(0, 0);
    LCD.println("Attempting MQTT");
    LCD.setCursor(0, 1);
    LCD.println("connection...");
    if (client.connect("esp32Client", mqtt_username, mqtt_password)) {
      Serial.println("connected");
      client.subscribe(mqtt_topic);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message received on topic: ");
  Serial.println(topic);
    // Flash the built-in LED when a message is received
  digitalWrite(builtInLedPin, HIGH);
  delay(250);  // LED on for 250 milliseconds
  digitalWrite(builtInLedPin, LOW);  // Turn off the LED

  String payloadStr = "";
  for (int i = 0; i < length; i++) {
    payloadStr += (char)payload[i];
  }

  int commaIndex = payloadStr.indexOf(',');
  if (commaIndex != -1) {
    String azimuthStr = payloadStr.substring(0, commaIndex);
    String altitudeStr = payloadStr.substring(commaIndex + 1);

    float azimuth = azimuthStr.toFloat();
    float altitude = altitudeStr.toFloat();

    // Map azimuth and altitude values to servo angles
    int panAngle = map(azimuth, 0, 360, 0, 180); // Map 0-360 to servo angle (0-180)
    int tiltAngle = map(altitude, 0, 90, 0, 180); // Map 0-90 to servo angle (0-180)

    // Set servo positions
    panServo.write(panAngle);
    tiltServo.write(tiltAngle);

    LCD.clear();
    LCD.setCursor(0, 0);
    LCD.println("Pan Angle:");
    LCD.println(panAngle);
    LCD.setCursor(0, 1);
    LCD.println("Tilt Angle:");
    LCD.println(tiltAngle);

    Serial.print("Azimuth: ");
    Serial.println(azimuth);
    Serial.print("Altitude: ");
    Serial.println(altitude);
    Serial.print("Pan Angle: ");
    Serial.println(panAngle);
    Serial.print("Tilt Angle: ");
    Serial.println(tiltAngle);

    delay(5000); //Delay between updates
  }
}
