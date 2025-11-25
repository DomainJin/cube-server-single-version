// ===== INCLUDES =====
#include <WiFi.h>
#include <OSCMessage.h>
#include <WiFiUdp.h>
#include <Adafruit_NeoPixel.h>

// ===== CONSTANTS =====
#define mainEffectTime 6000
#define operationTime 2000
#define LED_PIN 5
#define NUM_LEDS 150
#define UPDATE_INTERVAL 5  // ms

// ===== LED STRIP =====
Adafruit_NeoPixel strip(NUM_LEDS, LED_PIN, NEO_BGR + NEO_KHZ400);
// ===== NETW

// ===== NETWORK CONFIGURATION =====
const char* ssid = "Cube Touch";
const char* password = "admin123";

// UDP objects
WiFiUDP UdpPortSend;
WiFiUDP udp;

// OSC targets
const IPAddress resolume_ip(192, 168, 0, 241);
const unsigned int resolume_port = 7000;
const IPAddress laptop_ip(192, 168, 0, 159);
const unsigned int laptop_port = 7043;  // Port mới cho raw UDP
unsigned int localUdpPort = 4210;

// ===== GLOBAL VARIABLES =====
char incomingPacket[255];
int brightness = 255;  // Độ sáng mặc định (0-255)
int last_r = 43, last_g = 159, last_b = 2;  // Lưu màu cuối cùng
bool configMode = false;  // Config mode
bool touchProcessingDisabled = false;

// UART communication
String uartBuffer = "";
String uartLabel = "";
HardwareSerial SerialPIC(1);

// Touch state management
bool isTouched = false;
bool sentOSCOnce = false;
unsigned long touchStartMillis = 0;
unsigned long lastTouchDuration = 0;
int latestStatus = -1;
int latestValue = -1;

// OSC throttling
unsigned long lastOSCTime = 0;
const unsigned long OSC_INTERVAL = 100; // Send OSC maximum every 100ms
int lastSentStatus = -2;
int lastSentValue = -2;

// Effect control
bool waitingMainEffect = false;
bool waitInitAfterBack = false;
unsigned long mainEffectStartMillis = 0;
unsigned long timeCountdownInit = 0;
bool mainEffectStarted = false;

// LED control
int currentLedCount = 0;
unsigned long lastUpdateTime = 0;
bool effectEnable = true;
int ledDirection = 1;  // 1=normal, 0=reverse

// Rainbow effect variables
bool rainbowEffectActive = false;
unsigned long rainbowStartTime = 0;
int rainbowOffset = 0;

// ===== LED CONTROL FUNCTIONS =====
void applyColorWithBrightness(bool turnOn, int r, int g, int b) {
  if (!effectEnable) return;
  
  unsigned long now = millis();
  if (now - lastUpdateTime >= UPDATE_INTERVAL) {
    lastUpdateTime = now;
    
    // Update LED count
    if (turnOn && currentLedCount < NUM_LEDS) {
      currentLedCount++;
    } else if (!turnOn && currentLedCount > 0) {
      currentLedCount--;
    }
    
    // Calculate adjusted colors with brightness
    int adj_r = r * brightness / 255;
    int adj_g = g * brightness / 255;
    int adj_b = b * brightness / 255;
    
    // Apply colors based on direction
    for (int i = 0; i < NUM_LEDS; i++) {
      bool shouldLight = false;
      
      if (ledDirection == 1) {
        shouldLight = (i < currentLedCount);
      } else {
        shouldLight = (i >= NUM_LEDS - currentLedCount);
      }
      
      if (shouldLight) {
        strip.setPixelColor(i, strip.Color(adj_r, adj_g, adj_b));
      } else {
        strip.setPixelColor(i, strip.Color(0, 0, 0));
      }
    }
    
    strip.show();
  }
}

void disableEffect() {
  effectEnable = false;
  currentLedCount = 0;
  for (int i = 0; i < NUM_LEDS; i++) {
    strip.setPixelColor(i, strip.Color(0, 0, 0));
  }
  strip.show();
}

// ===== RAINBOW EFFECT FUNCTIONS =====
void startRainbowEffect() {
  rainbowEffectActive = true;
  rainbowStartTime = millis();
  rainbowOffset = 0;
  Serial.println("Rainbow effect started!");
}

void rainbowCaterpillarEffect(unsigned long durationMs) {
  unsigned long startTime = millis();
  int offset = 0;
  
  while (millis() - startTime < durationMs) {
    for (int i = 0; i < NUM_LEDS; i++) {
      uint8_t pixelHue = (offset + i * (255 / 7)) % 255;
      uint32_t color = strip.gamma32(strip.ColorHSV(pixelHue * 256));
      strip.setPixelColor(i, color);
    }
    strip.show();
    offset = (offset + 4) % 255;
    delay(UPDATE_INTERVAL);
  }
  
  // Clear all LEDs
  for (int i = 0; i < NUM_LEDS; i++) {
    strip.setPixelColor(i, 0);
  }
  strip.show();
}

void updateRainbowEffect() {
  if (!rainbowEffectActive) return;
  
  unsigned long elapsed = millis() - rainbowStartTime;
  if (elapsed >= mainEffectTime) {
    rainbowEffectActive = false;
    for (int i = 0; i < NUM_LEDS; i++) {
      strip.setPixelColor(i, 0);
    }
    strip.show();
    Serial.println("Rainbow effect finished!");
    return;
  }
  
  static unsigned long lastRainbowUpdate = 0;
  if (millis() - lastRainbowUpdate >= UPDATE_INTERVAL) {
    lastRainbowUpdate = millis();
    
    for (int i = 0; i < NUM_LEDS; i++) {
      uint8_t pixelHue = (rainbowOffset + i * (255 / 7)) % 255;
      uint32_t color = strip.gamma32(strip.ColorHSV(pixelHue * 256));
      strip.setPixelColor(i, color);
    }
    strip.show();
    rainbowOffset = (rainbowOffset + 4) % 255;
  }
}

// ===== OSC COMMUNICATION FUNCTIONS =====
void sendDebugUDPString(const String& message) {
  // Kiểm tra WiFi trước khi gửi
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[ERROR] WiFi disconnected! Cannot send UDP.");
    return;
  }
  
  // Gửi raw UDP message thay vì OSC
  int maxRetries = 3;
  bool sent = false;
  
  for (int retry = 0; retry < maxRetries && !sent; retry++) {
    int result = UdpPortSend.beginPacket(laptop_ip, laptop_port);
    if (result == 1) {
      UdpPortSend.print(message);
      int endResult = UdpPortSend.endPacket();
      if (endResult == 1) {
        sent = true;
        if (retry > 0) {
          Serial.printf("[UDP] Packet sent on retry %d\n", retry + 1);
        }
      } else {
        Serial.printf("[UDP ERROR] Failed to end packet (attempt %d)\n", retry + 1);
        delay(10);
      }
    } else {
      Serial.printf("[UDP ERROR] Failed to begin packet (attempt %d)\n", retry + 1);
      delay(10);
    }
  }
  
  if (!sent) {
    Serial.println("[UDP ERROR] Failed to send after all retries!");
  }
}

void sendResolumeEnableOSC(int durationMs) {
  // Kiểm tra WiFi
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[ERROR] WiFi disconnected! Cannot send Resolume OSC.");
    return;
  }
  
  Serial.print("[OSC->Resolume] Sending Enable commands to ");
  Serial.print(resolume_ip);
  Serial.print(":");
  Serial.println(resolume_port);
  
  unsigned long startTime = millis();
  while (millis() - startTime < durationMs) {
    // Layer 1
    OSCMessage msg1("/composition/layers/1/clear");
    msg1.add((int32_t)1);
    OSCMessage msg2("/composition/layers/1/clips/2/connect");
    msg2.add((int32_t)1);
    OSCMessage msg3("/composition/layers/1/clips/2/transport/position/behaviour/playdirection");
    msg3.add((int32_t)2);

    // Layer 2
    OSCMessage msg4("/composition/layers/2/clear");
    msg4.add((int32_t)1);
    OSCMessage msg5("/composition/layers/2/clips/2/connect");
    msg5.add((int32_t)1);
    OSCMessage msg6("/composition/layers/2/clips/2/transport/position/behaviour/playdirection");
    msg6.add((int32_t)2);

    // Layer 3
    OSCMessage msg7("/composition/layers/3/clear");
    msg7.add((int32_t)1);
    OSCMessage msg8("/composition/layers/3/clips/2/connect");
    msg8.add((int32_t)1);
    OSCMessage msg9("/composition/layers/3/clips/2/transport/position/behaviour/playdirection");
    msg9.add((int32_t)2);

    // Send all messages
    UdpPortSend.beginPacket(resolume_ip, resolume_port); msg1.send(UdpPortSend); UdpPortSend.endPacket(); msg1.empty();
    UdpPortSend.beginPacket(resolume_ip, resolume_port); msg2.send(UdpPortSend); UdpPortSend.endPacket(); msg2.empty();
    UdpPortSend.beginPacket(resolume_ip, resolume_port); msg3.send(UdpPortSend); UdpPortSend.endPacket(); msg3.empty();
    UdpPortSend.beginPacket(resolume_ip, resolume_port); msg4.send(UdpPortSend); UdpPortSend.endPacket(); msg4.empty();
    UdpPortSend.beginPacket(resolume_ip, resolume_port); msg5.send(UdpPortSend); UdpPortSend.endPacket(); msg5.empty();
    UdpPortSend.beginPacket(resolume_ip, resolume_port); msg6.send(UdpPortSend); UdpPortSend.endPacket(); msg6.empty();
    UdpPortSend.beginPacket(resolume_ip, resolume_port); msg7.send(UdpPortSend); UdpPortSend.endPacket(); msg7.empty();
    UdpPortSend.beginPacket(resolume_ip, resolume_port); msg8.send(UdpPortSend); UdpPortSend.endPacket(); msg8.empty();
    UdpPortSend.beginPacket(resolume_ip, resolume_port); msg9.send(UdpPortSend); UdpPortSend.endPacket(); msg9.empty();

    Serial.println("[OSC->Resolume] Enable clips sent successfully!");
  }
}

void sendResolumeInitOSC(int durationMs) {
  unsigned long startTime = millis();
  while (millis() - startTime < durationMs) {
    // Layer 1
    OSCMessage msga("/composition/layers/1/clips/1/connect");
    msga.add((int32_t)1);
    OSCMessage msgs("/composition/layers/1/clips/1/transport/position/behaviour/playdirection");
    msgs.add((int32_t)2);
    
    // Layer 2
    OSCMessage msgd("/composition/layers/2/clips/1/connect");
    msgd.add((int32_t)1);
    OSCMessage msgf("/composition/layers/2/clips/1/transport/position/behaviour/playdirection");
    msgf.add((int32_t)2);
    
    // Layer 3
    OSCMessage msgg("/composition/layers/3/clips/1/connect");
    msgg.add((int32_t)1);
    OSCMessage msgh("/composition/layers/3/clips/1/transport/position/behaviour/playdirection");
    msgh.add((int32_t)2);

    UdpPortSend.beginPacket(resolume_ip, resolume_port); msga.send(UdpPortSend); UdpPortSend.endPacket(); msga.empty();
    UdpPortSend.beginPacket(resolume_ip, resolume_port); msgs.send(UdpPortSend); UdpPortSend.endPacket(); msgs.empty();
    UdpPortSend.beginPacket(resolume_ip, resolume_port); msgd.send(UdpPortSend); UdpPortSend.endPacket(); msgd.empty();
    UdpPortSend.beginPacket(resolume_ip, resolume_port); msgf.send(UdpPortSend); UdpPortSend.endPacket(); msgf.empty();
    UdpPortSend.beginPacket(resolume_ip, resolume_port); msgg.send(UdpPortSend); UdpPortSend.endPacket(); msgg.empty();
    UdpPortSend.beginPacket(resolume_ip, resolume_port); msgh.send(UdpPortSend); UdpPortSend.endPacket(); msgh.empty();

    Serial.println("[OSC->Resolume] Init clips sent!");
  }
}

void sendResolumeBackOSC(int durationMs) {
  unsigned long startTime = millis();
  while (millis() - startTime < durationMs) {
    OSCMessage msgq("/composition/layers/1/clips/2/transport/position/behaviour/playdirection");
    msgq.add((int32_t)0);
    OSCMessage msgw("/composition/layers/2/clips/2/transport/position/behaviour/playdirection");
    msgw.add((int32_t)0);
    
    UdpPortSend.beginPacket(resolume_ip, resolume_port); msgq.send(UdpPortSend); UdpPortSend.endPacket(); msgq.empty();
    UdpPortSend.beginPacket(resolume_ip, resolume_port); msgw.send(UdpPortSend); UdpPortSend.endPacket(); msgw.empty();
    
    Serial.println("[OSC->Resolume] Back clips sent!");
  }
}

void sendResolumeMain(int durationMs) {
  unsigned long startTime = millis();
  while (millis() - startTime < durationMs) {
    OSCMessage msgz("/composition/layers/3/clips/3/connect");
    msgz.add((int32_t)1);
    OSCMessage msgx("/composition/layers/3/clips/3/transport/position/behaviour/playdirection");
    msgx.add((int32_t)2);

    UdpPortSend.beginPacket(resolume_ip, resolume_port); msgz.send(UdpPortSend); UdpPortSend.endPacket(); msgz.empty();
    UdpPortSend.beginPacket(resolume_ip, resolume_port); msgx.send(UdpPortSend); UdpPortSend.endPacket(); msgx.empty();

    Serial.println("[OSC->Resolume] Main effect sent!");
  }
}

// ===== TOUCH PROCESSING =====
void processTouch() {
  // Chỉ gửi OSC khi có thay đổi hoặc đủ thời gian throttle
  unsigned long currentTime = millis();
  bool shouldSendOSC = false;
  
  // Kiểm tra xem có thay đổi hay không
  if (latestStatus != lastSentStatus || latestValue != lastSentValue) {
    shouldSendOSC = true;
  } else if (currentTime - lastOSCTime >= OSC_INTERVAL) {
    shouldSendOSC = true; // Throttled periodic update
  }
  
  if (shouldSendOSC) {
    String debugMsg = "Val: " + String(latestValue) + " Thr: " + String(5147) + " Stt: " + String(latestStatus);
    sendDebugUDPString(debugMsg);
    lastOSCTime = currentTime;
    lastSentStatus = latestStatus;
    lastSentValue = latestValue;
  }
  
  // Xử lý touch logic chỉ khi không bị disable
  if (touchProcessingDisabled || latestStatus == -1) {
    return;
  }
  
  if (latestStatus == 1) {
    if (!isTouched) {
      isTouched = true;
      sentOSCOnce = false;
      touchStartMillis = millis();
      Serial.println("[TOUCH] Touch detected!");
    }
    if (!sentOSCOnce) {
      Serial.println("[TOUCH] Sending EnableOSC...");
      sendResolumeEnableOSC(5);
      sentOSCOnce = true;
    }
  } else {
    if (isTouched) {
      isTouched = false;
      sentOSCOnce = false;
      lastTouchDuration = millis() - touchStartMillis;
      Serial.printf("[TOUCH] Touch released, duration: %lums\n", lastTouchDuration);

      if (lastTouchDuration < operationTime && lastTouchDuration > 0) {
        timeCountdownInit = millis();
        Serial.println("[TOUCH] Sending BackOSC (short touch)...");
        sendResolumeBackOSC(5);
        waitInitAfterBack = true;
      }
      else if (lastTouchDuration >= operationTime) {
        Serial.println("[TOUCH] Triggering main effect (long touch)...");
        sendResolumeMain(5);
        waitingMainEffect = true;
        mainEffectStartMillis = millis();
      }
    }
  }
  
  // Reset status sau khi xử lý
  latestStatus = -1;
}

// ===== SETUP FUNCTION =====
void setup() {
  // Initialize LED strip
  strip.begin();
  strip.show();
  strip.setBrightness(brightness);

  // Initialize serial communication
  Serial.begin(115200);
  SerialPIC.begin(9600, SERIAL_8N1, 33, 26);

  Serial.println("ESP32 Ready to receive from PIC!");
  
  // Debug thông tin WiFi
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  int attempt = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    attempt++;
    if (attempt > 30) {
      Serial.println("Kết nối WiFi thất bại!");
      while(1);
    }
  }
  
  Serial.println("\nWiFi connected!");
  Serial.print("Local IP: "); Serial.println(WiFi.localIP());
  
  // Debug thông tin OSC
  Serial.print("OSC Target - Laptop: ");
  Serial.print(laptop_ip);
  Serial.print(":");
  Serial.println(laptop_port);
  
  Serial.print("OSC Target - Resolume: ");
  Serial.print(resolume_ip);
  Serial.print(":");
  Serial.println(resolume_port);
  
  UdpPortSend.begin(9000);
  udp.begin(localUdpPort);
  Serial.printf("Listening UDP on port %d\n", localUdpPort);
  
  // Test gửi OSC đầu tiên
  sendDebugOSCString("ESP32 Started - OSC Test");
}

// ===== MAIN LOOP =====
void loop() {
  // ===== UDP COMMAND PROCESSING =====
  int packetSize = udp.parsePacket();
  if (packetSize) {
    int len = udp.read(incomingPacket, 254);
    incomingPacket[len] = 0;
    Serial.printf("Received: %s\n", incomingPacket);
    
    // Config mode commands
    if (strncmp(incomingPacket, "CONFIG:", 7) == 0) {
      int configState = atoi(incomingPacket + 7);
      configMode = (configState == 1);
      if (configMode) {
        touchProcessingDisabled = true;
        effectEnable = true;
      } else {
        touchProcessingDisabled = false;
      }
      Serial.printf("Config Mode: %s\n", configMode ? "ON" : "OFF");
    }
    
    // LED control commands (config mode only)
    else if (strncmp(incomingPacket, "LEDCTRL:", 8) == 0 && configMode) {
      String command = String(incomingPacket + 8);
      int firstComma = command.indexOf(',');
      int secondComma = command.indexOf(',', firstComma + 1);
      int thirdComma = command.indexOf(',', secondComma + 1);
      
      if (firstComma > 0 && secondComma > 0 && thirdComma > 0) {
        String indexStr = command.substring(0, firstComma);
        int r = command.substring(firstComma + 1, secondComma).toInt();
        int g = command.substring(secondComma + 1, thirdComma).toInt();
        int b = command.substring(thirdComma + 1).toInt();
        
        if (indexStr == "ALL") {
          for (int i = 0; i < NUM_LEDS; i++) {
            strip.setPixelColor(i, strip.Color(r, g, b));
          }
        } else {
          int index = indexStr.toInt();
          if (index >= 0 && index < NUM_LEDS) {
            strip.setPixelColor(index, strip.Color(r, g, b));
          }
        }
        strip.show();
        Serial.printf("Direct LED Control: %s R=%d G=%d B=%d\n", indexStr.c_str(), r, g, b);
      }
    }
    
    // Rainbow effect (config mode only)
    else if (strcmp(incomingPacket, "RAINBOW:START") == 0 && configMode) {
      startRainbowEffect();
      Serial.println("Rainbow effect started via config mode");
    }
    
    // LED enable/disable
    else if (strncmp(incomingPacket, "LED:", 4) == 0) {
      int ledState = atoi(incomingPacket + 4);
      effectEnable = (ledState == 1);
      if (!effectEnable) {
        for (int i = 0; i < NUM_LEDS; i++) {
          strip.setPixelColor(i, strip.Color(0, 0, 0));
        }
        strip.show();
        currentLedCount = 0;
      }
      Serial.printf("LED Control: %s\n", effectEnable ? "ON" : "OFF");
    }
    
    // LED direction control
    else if (strncmp(incomingPacket, "DIR:", 4) == 0) {
      int direction = atoi(incomingPacket + 4);
      ledDirection = (direction == 1) ? 1 : 0;
      Serial.printf("LED Direction: %d\n", ledDirection);
    }
    
    // Threshold setting
    else if (strncmp(incomingPacket, "THRESHOLD:", 10) == 0) {
      int thresholdValue = atoi(incomingPacket + 10);
      SerialPIC.print("THRESHOLD:");
      SerialPIC.print(thresholdValue);
      SerialPIC.print("\n");
      Serial.printf("Sent threshold to PIC: %d\n", thresholdValue);
    }
    
    // Brightness control
    else if (strcmp(incomingPacket, "UP") == 0) {
      brightness += 16;
      if (brightness > 255) brightness = 255;
      Serial.printf("Brightness UP: %d\n", brightness);
    }
    else if (strcmp(incomingPacket, "DOWN") == 0) {
      brightness -= 16;
      if (brightness < 1) brightness = 1;
      Serial.printf("Brightness DOWN: %d\n", brightness);
    }
    
    // Color setting
    else {
      int r, g, b;
      if (sscanf(incomingPacket, "%d %d %d", &r, &g, &b) == 3) {
        last_r = r; last_g = g; last_b = b;
        Serial.printf("Set color: R=%d G=%d B=%d, Brightness=%d\n", r, g, b, brightness);
      }
    }
  }

  // ===== EFFECT UPDATES =====
  updateRainbowEffect();
  
  if (!rainbowEffectActive) {
    strip.setBrightness(brightness);
    applyColorWithBrightness(isTouched, last_r, last_g, last_b);
  }

  // ===== TOUCH LOGIC =====
  if (isTouched && !mainEffectStarted && (millis() - touchStartMillis >= operationTime)) {
    waitingMainEffect = true;
    mainEffectStarted = true;
    Serial.println("Set waitingMainEffect = true (chạm đủ lâu)");
  }

  if (waitingMainEffect) {
    effectEnable = false;
    sendResolumeMain(5);
    Serial.print(" | Main effect triggered!");
    rainbowCaterpillarEffect(mainEffectTime);
    Serial.println("[OSC->Resolume] Main effect started, non-blocking rainbow.");
    sendResolumeInitOSC(5);
    touchStartMillis = 0;
    waitingMainEffect = false;
    mainEffectStarted = false;  
    effectEnable = true;
    isTouched = false;
    sentOSCOnce = false;
    latestStatus = -1;
    latestValue = -1;
  }

  if (waitInitAfterBack && millis() >= timeCountdownInit + lastTouchDuration) {
    sendResolumeInitOSC(5);
    waitInitAfterBack = false;
    Serial.println("[OSC->Resolume] InitOSC sent after BackOSC delay!");
  }

  // ===== UART PROCESSING =====
  while (SerialPIC.available()) {
    char c = SerialPIC.read();
    if (c == '\n') {
      uartBuffer.trim();
      
      if (uartBuffer == "value") {
        uartLabel = "value";
      } else if (uartBuffer == "status") {
        uartLabel = "status";
      } else {
        bool dataUpdated = false;
        
        if (uartLabel == "value") {
          int newValue = uartBuffer.toInt();
          if (newValue != latestValue) {
            latestValue = newValue;
            dataUpdated = true;
          }
        } else if (uartLabel == "status") {
          int newStatus = uartBuffer.toInt();
          if (newStatus != latestStatus) {
            latestStatus = newStatus;
            dataUpdated = true;
          }
        }
        
        uartLabel = "";
        
        // Chỉ xử lý touch khi có data mới và không bị disable
        if (dataUpdated && !touchProcessingDisabled) {
          processTouch();
        }
      }
      uartBuffer = "";
    } else {
      uartBuffer += c;
    }
  }
}