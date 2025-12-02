#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <WiFi.h> // <--- 1. LIBRERÍA NECESARIA AGREGADA

// --- Pines I2C del ESP32 ---
#define SDA_PIN 21
#define SCL_PIN 22

// --- Pin del botón para el contador ---
#define BUTTON_PIN 4

// --- Configuración del display ---
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET    -1
#define SCREEN_ADDRESS 0x3C

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
Adafruit_BME280 bme;

// --- Variables para fecha y hora ---
unsigned long startTime;
// --- Variables para el contador y botón ---
int contador = 0;
// 0=Todos, 1=Solo Temp, 2=Solo Hum, 3=Solo Pres, 4=Pelón
int lastButtonState = HIGH;
int buttonState;
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 50;

// Declaración adelantada de funciones
void mostrarTodosDatos(float temp, float hum, float pres);
void mostrarSoloTemperatura(float temp);
void mostrarSoloHumedad(float hum);
void mostrarSoloPresion(float pres);
void mostrarLogoPelon();

void setup() {
  Serial.begin(115200);
  
  // Configurar pin del botón
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  
  // Inicializa I2C con pines personalizados del ESP32
  Wire.begin(SDA_PIN, SCL_PIN);
  
  // Inicializa la pantalla
  if (!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println(F("SSD1306 allocation failed"));
    while (1);
  }

  // Inicializa sensor BME280
  if (!bme.begin(0x76)) { // Intenta 0x76 primero
     if (!bme.begin(0x77)) { // Si falla, intenta 0x77
        Serial.println(F("Could not find a valid BME280 sensor!"));
        display.clearDisplay();
        display.setTextSize(1);
        display.setTextColor(SSD1306_WHITE);
        display.setCursor(0,0);
        display.println("ERROR BME280");
        display.display();
        while (1);
     }
  }

  // --- 2. OBTENER Y ENVIAR MAC ADDRESS (IDENTIFICADOR ÚNICO) ---
  String mac = WiFi.macAddress();
  // Pequeña pausa para asegurar que el puerto serial esté listo
  delay(100); 
  Serial.println(); // Limpiar basura del buffer
  Serial.print("ID_THB:");
  Serial.println(mac);
  // -------------------------------------------------------------

  // Pantalla de inicio (Original Pelón)
  display.clearDisplay();
  display.setTextSize(2);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0,10);
  display.println("BME280");
  display.setCursor(0,35);
  display.println("ACTIVO");
  display.display();
  delay(2000);

  startTime = millis();
  
  // Encabezado para Python
  Serial.println("INICIO,TEMPERATURA,HUMEDAD,PRESION");
}

void loop() {
  // Leer datos del sensor
  float temperatura = bme.readTemperature();
  float humedad = bme.readHumidity();
  float presion = bme.readPressure() / 100.0F;

  // --- Manejo del botón con debounce ---
  int reading = digitalRead(BUTTON_PIN);
  if (reading != lastButtonState) {
    lastDebounceTime = millis();
  }
  
  if ((millis() - lastDebounceTime) > debounceDelay) {
    if (reading != buttonState) {
      buttonState = reading;
      // Cuando el botón se presiona (va de HIGH a LOW)
      if (buttonState == LOW) {
        contador++;
        if (contador > 4) {
          contador = 0;
        }
      }
    }
  }
  lastButtonState = reading;
  
  // Calcular tiempo transcurrido
  unsigned long tiempo = millis() - startTime;
  int horas = (tiempo / 3600000) % 24;
  int minutos = (tiempo / 60000) % 60;
  int segundos = (tiempo / 1000) % 60;
  
  // Mostrar en pantalla según el contador
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  
  // Fecha y hora (simulada) - siempre visible
  display.setCursor(0, 0);
  display.print("18/10/2024 ");
  if (horas < 10) display.print("0");
  display.print(horas);
  display.print(":");
  if (minutos < 10) display.print("0");
  display.print(minutos);
  display.print(":");
  if (segundos < 10) display.print("0");
  display.print(segundos);

  // Mostrar modo actual
  display.setCursor(90, 0);
  display.print("M:");
  display.print(contador);

  // Línea separadora
  display.drawLine(0, 10, 128, 10, SSD1306_WHITE);
  
  // --- Mostrar datos según el contador ---
  switch(contador) {
    case 0: // Todos los datos
      mostrarTodosDatos(temperatura, humedad, presion);
      break;
    case 1: // Solo temperatura
      mostrarSoloTemperatura(temperatura);
      break;
    case 2: // Solo humedad
      mostrarSoloHumedad(humedad);
      break;
    case 3: // Solo presión
      mostrarSoloPresion(presion);
      break;
    case 4: // Logo pelón
      mostrarLogoPelon();
      break;
  }

  display.display();
  
  // ENVÍO A PYTHON 
  // Formato: timestamp,temperatura,humedad,presion
  Serial.print(millis());
  Serial.print(",");
  Serial.print(temperatura, 2);  // 2 decimales
  Serial.print(",");
  Serial.print(humedad, 2);     // 2 decimales
  Serial.print(",");
  Serial.println(presion, 2);
  
  delay(200);  
}

// --- Funciones auxiliares (Originales) ---

void mostrarTodosDatos(float temp, float hum, float pres) {
  display.setCursor(0, 15);
  display.setTextSize(2);
  display.print("Temp: "); display.print(temp, 1); display.println(" C");

  display.setCursor(0, 35);
  display.print("Hum:  "); display.print(hum, 1); display.println(" %");
  
  display.setCursor(0, 55);
  display.setTextSize(1);
  display.print("Pres: "); display.print(pres, 0); display.println(" hPa");
}

void mostrarSoloTemperatura(float temp) {
  display.setCursor(0, 25);
  display.setTextSize(3);
  display.print(temp, 1);
  display.setTextSize(2);
  display.println(" C");
  display.setTextSize(1);
  display.setCursor(0, 55);
  display.print("TEMPERATURA");
}

void mostrarSoloHumedad(float hum) {
  display.setCursor(0, 25);
  display.setTextSize(3);
  display.print(hum, 1);
  display.setTextSize(2);
  display.println(" %");
  display.setTextSize(1);
  display.setCursor(0, 55);
  display.print("HUMEDAD");
}

void mostrarSoloPresion(float pres) {
  display.setCursor(0, 25);
  display.setTextSize(3);
  display.print(pres, 0);
  display.setTextSize(2);
  display.println(" hPa");
  display.setTextSize(1);
  display.setCursor(0, 55);
  display.print("PRESION");
}

void mostrarLogoPelon() {
  display.drawCircle(64, 32, 20, SSD1306_WHITE);
  display.fillCircle(56, 28, 3, SSD1306_WHITE);  // Ojo izquierdo
  display.fillCircle(72, 28, 3, SSD1306_WHITE);  // Ojo derecho
  display.drawLine(58, 40, 70, 40, SSD1306_WHITE);
  display.drawPixel(57, 39, SSD1306_WHITE);
  display.drawPixel(71, 39, SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(50, 55);
  display.print("PELON");
  display.drawLine(60, 18, 68, 18, SSD1306_WHITE);
  display.drawLine(58, 20, 70, 20, SSD1306_WHITE);
}