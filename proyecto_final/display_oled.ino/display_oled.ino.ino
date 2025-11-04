#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_BME280.h>

// --- Configuración de Pantalla OLED (I2C) ---
#define SCREEN_WIDTH 128 // Ancho en píxeles
#define SCREEN_HEIGHT 64 // Alto en píxeles
#define OLED_RESET -1 // Pin de Reset (-1 si comparte pin de reset de Arduino)
#define SCREEN_ADDRESS 0x3C // Dirección I2C de la pantalla (la más común)
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// --- Configuración del Sensor BME280 (I2C) ---
Adafruit_BME280 bme; // Objeto I2C

void setup() {
  Serial.begin(115200); // Iniciar monitor serial para depuración

  // --- Inicializar Pantalla OLED ---
  if(!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println(F("Error: No se pudo inicializar la pantalla SSD1306"));
    for(;;); // Bucle infinito si falla
  }
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0,0);
  display.println(F("Termohigrobarometro"));
  display.println(F("Inicializando..."));
  display.display();
  delay(2000);

  // --- Inicializar Sensor BME280 ---
  if (!bme.begin(0x76)) { // 0x76 es la dirección I2C más común para el BME280
    Serial.println(F("Error: No se pudo encontrar el sensor BME280"));
    display.clearDisplay();
    display.setCursor(0,0);
    display.println(F("Error de Sensor"));
    display.println(F("BME280 no detectado."));
    display.display();
    for(;;); // Bucle infinito si falla
  }
  Serial.println(F("Sensor BME280 detectado!"));
}

void loop() {
  // Leer los valores del sensor
  // Para el SI, la presión debe estar en Pascales (Pa)
  float temperatura_c = bme.readTemperature(); // Lee en °C por defecto
  float humedad_rel = bme.readHumidity();     // Lee en %
  float presion_pa = bme.readPressure();      // Lee en Pascales (Pa)

  // --- Mostrar en el Monitor Serial (para depuración) ---
  Serial.print(F("Temperatura: ")); Serial.print(temperatura_c); Serial.println(F(" *C"));
  Serial.print(F("Humedad: ")); Serial.print(humedad_rel); Serial.println(F(" %"));
  Serial.print(F("Presion: ")); Serial.print(presion_pa); Serial.println(F(" Pa"));

  // --- Mostrar en la Pantalla OLED ---
  display.clearDisplay();
  display.setCursor(0, 0); // Volver al inicio

  // Fila 1: Título
  display.setTextSize(2);
  display.println(F("DATOS"));
  display.setTextSize(1);
  display.println(F("---------------------"));

  // Fila 2: Temperatura
  display.setTextSize(2);
  display.print(temperatura_c, 1); // El ", 1" es para 1 decimal
  display.setTextSize(1);
  display.cp.print((char)247); // Símbolo de grados °
  display.setTextSize(2);
  display.println(F("C"));
  
  // Fila 3: Humedad
  display.setTextSize(2);
  display.print(humedad_rel, 0); // 0 decimales
  display.println(F(" %"));

  // Fila 4: Presión (en hPa para que quepa mejor)
  display.setTextSize(1);
  display.print(F("Presion: "));
  display.print(presion_pa / 100.0, 1); // Convertir Pa a hPa (milibares)
  display.println(F(" hPa"));
  
  display.display(); // Enviar todo el buffer a la pantalla

  delay(2000); // Tiempo de muestreo de 2 segundos (luego lo haremos variable)
}