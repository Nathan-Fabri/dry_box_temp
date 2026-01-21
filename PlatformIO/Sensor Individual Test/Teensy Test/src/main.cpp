#include <Arduino.h>

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);

  Serial.begin(9600);
  while (!Serial) {
    ; // Wait for Serial to open (necessary on Teensy)
  }

  Serial.println("Use UP arrow to turn LED ON and DOWN arrow to turn LED OFF.");
}

void loop() {
  static int state = 0; // 0 = waiting for ESC, 1 = waiting for '[', 2 = waiting for command
  static char seq[3];

  if (Serial.available()) {
    char c = Serial.read();

    switch (state) {
      case 0:
        if (c == 0x1B) { // ESC
          state = 1;
        }
        break;
      case 1:
        if (c == '[') {
          state = 2;
        } else {
          state = 0;
        }
        break;
      case 2:
        if (c == 'A') { // UP arrow
          digitalWrite(LED_BUILTIN, HIGH);
          Serial.println("LED ON");
        } else if (c == 'B') { // DOWN arrow
          digitalWrite(LED_BUILTIN, LOW);
          Serial.println("LED OFF");
        }
        state = 0;
        break;
      default:
        state = 0;
        break;
    }
  }
}
