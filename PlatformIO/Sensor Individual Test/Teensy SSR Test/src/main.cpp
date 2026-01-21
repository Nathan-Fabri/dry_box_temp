#include <Arduino.h>

void setup() {
  Serial.begin(115200);
  pinMode(9, OUTPUT);
  digitalWrite(9, LOW);  // Start LOW
  Serial.println("Press 'h' to set pin 9 HIGH, 'l' to set it LOW");
}

void loop() {
  if (Serial.available()) {
    char c = Serial.read();

    if (c == 'h') {
      digitalWrite(9, HIGH);
      Serial.println("Pin 9 set HIGH");
    } else if (c == 'l') {
      digitalWrite(9, LOW);
      Serial.println("Pin 9 set LOW");
    }
  }
}
