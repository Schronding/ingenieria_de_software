#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <WiFi.h>

#define SDA_PIN 21
#define SCL_PIN 22
#define BUTTON_PIN 4
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
Adafruit_BME280 bme;

// Variables
unsigned long startTime;
// Variables Hora
int realHour = 0, realMin = 0, realSec = 0;
unsigned long lastTimeSync = 0;

int contador = 0; 
int lastButtonState = HIGH;
int buttonState;
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 50;
String macAddress; 

void mostrarSoloTemperatura(float tempC);
void mostrarSoloHumedad(float hum);
void mostrarSoloPresion(float presHPa);
void mostrarLogoPelon();

void setup() {
  Serial.begin(115200);
  // --- FIX CRÍTICO: Timeout corto para no bloquear datos ---
  Serial.setTimeout(50); 
  // --------------------------------------------------------
  
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  WiFi.mode(WIFI_STA); 

  Wire.begin(SDA_PIN, SCL_PIN);
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { for(;;); }

  if (!bme.begin(0x76)) { 
     if (!bme.begin(0x77)) {
        display.clearDisplay(); display.println("Error Sensor"); display.display(); while (1);
     }
  }

  macAddress = WiFi.macAddress();
  
  // Pantalla de carga
  display.clearDisplay();
  display.setTextSize(1); display.setTextColor(WHITE);
  display.setCursor(0,10); display.println("SISTEMA PELON");
  display.setCursor(0,30); display.println("ID MAC:");
  display.setCursor(0,45); display.println(macAddress);
  display.display();
  delay(1000);

  startTime = millis();
  lastTimeSync = millis(); 
}

void loop() {
  // --- 1. LECTURA NO BLOQUEANTE DE HORA ---
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim(); // Quitar espacios basura
    if (input.startsWith("T:")) {
      realHour = input.substring(2, 4).toInt();
      realMin = input.substring(5, 7).toInt();
      realSec = input.substring(8, 10).toInt();
      lastTimeSync = millis(); 
    }
  }

  // Actualizar reloj local
  unsigned long delta = (millis() - lastTimeSync) / 1000;
  long totalSec = realHour * 3600L + realMin * 60L + realSec + delta;
  int currentSec = totalSec % 60;
  int currentMin = (totalSec / 60) % 60;
  int currentHour = (totalSec / 3600) % 24;

  float tempC = bme.readTemperature();
  float hum = bme.readHumidity();
  float presHPa = bme.readPressure() / 100.0F; 

  // --- 2. ENVIAR DATOS (ID SIEMPRE PRIMERO) ---
  // IMPORTANTE: Enviamos todo en una sola línea o en bloque compacto
  Serial.print("ID:"); Serial.println(macAddress);
  
  // Datos: Timestamp, Temp, Hum, Pres
  Serial.print(millis()); Serial.print(",");
  Serial.print(tempC, 2); Serial.print(",");
  Serial.print(hum, 2); Serial.print(",");
  Serial.println(presHPa, 2);

  // Lógica Botón
  int reading = digitalRead(BUTTON_PIN);
  if (reading != lastButtonState) lastDebounceTime = millis();
  if ((millis() - lastDebounceTime) > debounceDelay) {
    if (reading != buttonState) {
      buttonState = reading;
      if (buttonState == LOW) {
        contador++;
        if (contador > 3) contador = 0; 
      }
    }
  }
  lastButtonState = reading;
  
  // Renderizado OLED
  display.clearDisplay();
  display.setTextSize(1); display.setTextColor(WHITE);
  
  display.setCursor(0, 0);
  if (currentHour < 10) display.print("0"); display.print(currentHour); display.print(":");
  if (currentMin < 10) display.print("0"); display.print(currentMin); display.print(":");
  if (currentSec < 10) display.print("0"); display.print(currentSec);

  display.setCursor(100, 0); display.print("M:"); display.print(contador);
  display.drawLine(0, 10, 128, 10, WHITE);
  
  switch(contador) {
    case 0: mostrarSoloTemperatura(tempC); break;
    case 1: mostrarSoloHumedad(hum); break;
    case 2: mostrarSoloPresion(presHPa); break;
    case 3: mostrarLogoPelon(); break;
  }
  display.display();
  delay(500); // 0.5s para mayor fluidez
}

// Funciones Auxiliares (SI Units)
void mostrarSoloTemperatura(float tempC) {
  float tempK = tempC + 273.15;
  display.setCursor(0, 25); display.setTextSize(3);
  display.print(tempK, 1); display.setTextSize(2); display.println(" K");
  display.setTextSize(1); display.setCursor(0, 55); display.print("TEMP (SI)");
}
void mostrarSoloHumedad(float hum) {
  display.setCursor(0, 25); display.setTextSize(3);
  display.print(hum, 1); display.setTextSize(2); display.println(" %");
  display.setTextSize(1); display.setCursor(0, 55); display.print("HUMEDAD");
}
void mostrarSoloPresion(float presHPa) {
  float presPa = presHPa * 100.0;
  display.setCursor(0, 25); display.setTextSize(2); 
  display.print(presPa, 0); display.println(" Pa");
  display.setTextSize(1); display.setCursor(0, 55); display.print("PRESION (SI)");
}
void mostrarLogoPelon() {
  display.drawCircle(64, 32, 20, WHITE);
  display.fillCircle(56, 28, 3, WHITE);
  display.fillCircle(72, 28, 3, WHITE);
  display.drawPixel(57, 39, WHITE); display.drawPixel(71, 39, WHITE);
  display.drawLine(58, 40, 70, 40, WHITE);
  display.setTextSize(1); display.setCursor(50, 55); display.print("PELON");
  display.drawLine(60, 18, 68, 18, WHITE); display.drawLine(58, 20, 70, 20, WHITE);
}