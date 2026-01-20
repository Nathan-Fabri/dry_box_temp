#ifndef LOAD_CELL_H
#define LOAD_CELL_H

#include <Arduino.h>

// Function declarations
void setupLoadCell();
float readLoadCellWeight();
void debugPrintLoadCell();
float getLoadCellWeight();

#endif // LOAD_CELL_H 