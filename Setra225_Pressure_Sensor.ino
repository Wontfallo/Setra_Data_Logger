#include <Arduino.h>

/*
  Arduino Sketch for Setra Model 225 (4-20mA Output) Pressure Sensor
  Reads the sensor's current output by converting it to a voltage
  with a 250-ohm resistor and then calculates the pressure in Bar.

  !! REQUIRED HARDWARE SETUP FOR 4-20mA SENSOR !!
  - Sensor: Setra 225, PN 225G1R7BAC411, 0-1.7 Bar, 4-20mA Output.
  - Power: Power the sensor with an appropriate DC voltage (e.g., 10-30V).
  - Resistor: A precision 250-ohm resistor is REQUIRED.
  - Wiring:
    1. Connect the sensor's output wire to one side of the 250-ohm resistor.
    2. Connect that same point (sensor output & resistor) to Arduino pin A0.
    3. Connect the other side of the resistor to Arduino GND.
    4. Connect the sensor's power supply ground to Arduino GND.

  This circuit converts the 4-20mA current signal into a 1-5V voltage signal
  that the Arduino can safely read on its analog pin.
*/

// === SENSOR CALIBRATION - Based on your specific sensor ===
// PN: 225G1R7BAC411
// Pressure Range: 0 to 1.7 Bar
const float MIN_PRESSURE = 0.0;
const float MAX_PRESSURE = 1.7;

// Output: 4-20mA, which is converted to 1-5V by a 250-ohm resistor.
// 4mA  * 250Ω = 1.0V
// 20mA * 250Ω = 5.0V
const float MIN_VOLTAGE = 1.0;
const float MAX_VOLTAGE = 5.0;
// ============================================================


// The analog pin the sensor is connected to
const int SENSOR_PIN = A0;

void setup() {
  // Initialize serial communication at 9600 bits per second:
  Serial.begin(9600);
  Serial.println("Setra 225 Pressure Sensor Reading");
  Serial.println("---------------------------------");
}

void loop() {
  // Read the raw analog value from the sensor (0-1023)
  int rawValue = analogRead(SENSOR_PIN);

  // Convert the raw analog value (0-1023) to a voltage (1-5V)
  float voltage = rawValue * (5.0 / 1023.0);

  // Map the voltage (1-5V) to the pressure range (0-1.7 Bar)
  float pressure = MIN_PRESSURE + ((voltage - MIN_VOLTAGE) * (MAX_PRESSURE - MIN_PRESSURE)) / (MAX_VOLTAGE - MIN_VOLTAGE);

  // Ensure the pressure reading does not go below the minimum, which can happen
  // with slight fluctuations when the reading is at the minimum voltage.
  if (pressure < MIN_PRESSURE) {
    pressure = MIN_PRESSURE;
  }

  // Send just the pressure value over serial, followed by a newline.
  // This makes it easy for other programs (like our Python script) to read.
  Serial.println(pressure, 4); // Print with 4 decimal places for better resolution

  // Wait for a short moment before the next reading for the dashboard
  delay(200);
}