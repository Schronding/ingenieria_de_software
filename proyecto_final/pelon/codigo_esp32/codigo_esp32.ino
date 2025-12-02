#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <WiFi.h>

// --- Configuración ---
#define SDA_PIN 21
#define SCL_PIN 22
#define BUTTON_PIN 4
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
Adafruit_BME280 bme;

// Variables
unsigned long startTime;
int contador = 0; // 0=Temp(K), 1=Hum(%), 2=Pres(Pa), 3=Pelón
int lastButtonState = HIGH;
int buttonState;
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 50;

// Declaración de funciones
void mostrarSoloTemperatura(float tempC);
void mostrarSoloHumedad(float hum);
void mostrarSoloPresion(float presHPa);
void mostrarLogoPelon();

void setup() {
  Serial.begin(115200);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  
  Wire.begin(SDA_PIN, SCL_PIN);
  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    Serial.println(F("Error OLED")); while (1);
  }

  // Inicialización BME280 (Intento doble dirección)
  if (!bme.begin(0x76)) { 
     if (!bme.begin(0x77)) {
        display.clearDisplay();
        display.setCursor(0,0); display.println("Error Sensor"); display.display();
        while (1);
     }
  }

  // --- ESTRATEGIA DE SINCRONIZACIÓN DE ID (5 SEGUNDOS) ---
  String mac = WiFi.macAddress();
  unsigned long inicioID = millis();
  
  // Bucle de 5 segundos enviando el ID constantemente
  while(millis() - inicioID < 5000) {
    Serial.println(); // Salto de línea para limpiar
    Serial.print("ID_THB:");
    Serial.println(mac);
    
    // Mostrar cuenta regresiva en pantalla
    display.clearDisplay();
    display.setTextSize(2); display.setTextColor(WHITE);
    display.setCursor(0,0); display.println("CONECTA YA");
    display.setTextSize(1);
    display.setCursor(0,30); display.println("Enviando ID a PC...");
    display.setCursor(0,45); display.print("MAC: "); display.println(mac);
    display.setCursor(0,55); display.print("Tiempo: "); display.print(5 - (millis() - inicioID)/1000); display.println("s");
    display.display();
    
    delay(500); // Enviar cada medio segundo
  }
  // -------------------------------------------------------

  startTime = millis();
  // Encabezado
  Serial.println("INICIO,TEMPERATURA,HUMEDAD,PRESION");
}

void loop() {
  // Lectura de Sensores
  float tempC = bme.readTemperature();
  float hum = bme.readHumidity();
  float presHPa = bme.readPressure() / 100.0F; 

  // --- Botón ---
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
  
  // --- Calcular Tiempo ---
  unsigned long tiempo = millis() - startTime;
  int horas = (tiempo / 3600000) % 24;
  int minutos = (tiempo / 60000) % 60;
  int segundos = (tiempo / 1000) % 60;
  
  // --- Renderizado Header ---
  display.clearDisplay();
  display.setTextSize(1); display.setTextColor(WHITE);
  display.setCursor(0, 0);
  if (horas < 10) display.print("0"); display.print(horas); display.print(":");
  if (minutos < 10) display.print("0"); display.print(minutos); display.print(":");
  if (segundos < 10) display.print("0"); display.print(segundos);
  display.setCursor(100, 0); display.print("M:"); display.print(contador);
  display.drawLine(0, 10, 128, 10, WHITE);
  
  // --- Switch de Vistas (AHORA EN UNIDADES SI) ---
  switch(contador) {
    case 0: mostrarSoloTemperatura(tempC); break;
    case 1: mostrarSoloHumedad(hum); break;
    case 2: mostrarSoloPresion(presHPa); break;
    case 3: mostrarLogoPelon(); break;
  }

  display.display();
  
  // --- Envío a Python (Mantenemos °C y hPa para compatibilidad con DB) ---
  Serial.print(millis()); Serial.print(",");
  Serial.print(tempC, 2); Serial.print(",");
  Serial.print(hum, 2); Serial.print(",");
  Serial.println(presHPa, 2);
  
  delay(200);  
}

// --- Funciones de Pantalla (CONVERTIDAS A SI) ---

void mostrarSoloTemperatura(float tempC) {
  // Convertir a KELVIN para visualización
  float tempK = tempC + 273.15;
  
  display.setCursor(0, 25); display.setTextSize(3);
  display.print(tempK, 1); display.setTextSize(2); display.println(" K");
  display.setTextSize(1); display.setCursor(0, 55); display.print("TEMPERATURA (SI)");
}

void mostrarSoloHumedad(float hum) {
  display.setCursor(0, 25); display.setTextSize(3);
  display.print(hum, 1); display.setTextSize(2); display.println(" %");
  display.setTextSize(1); display.setCursor(0, 55); display.print("HUMEDAD");
}

void mostrarSoloPresion(float presHPa) {
  // Convertir a PASCALES para visualización (hPa * 100)
  float presPa = presHPa * 100.0;
  
  // Ajuste de tamaño para que quepa el número grande (ej. 101325)
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