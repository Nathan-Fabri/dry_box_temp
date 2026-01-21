#!/bin/bash
# Development flash script for Teensy controllers
TARGET=${1:-all}
echo "----------------------------------------------" >> "/home/fbr-pi/software/Drybox/drybox/RPI5/DataLogging/dev/teensy_flash.log"
echo "Mock flashing Teensy $TARGET at $(date)" >> "/home/fbr-pi/software/Drybox/drybox/RPI5/DataLogging/dev/teensy_flash.log"
echo "----------------------------------------------" >> "/home/fbr-pi/software/Drybox/drybox/RPI5/DataLogging/dev/teensy_flash.log"
echo "Development mode - simulating flash operation" >> "/home/fbr-pi/software/Drybox/drybox/RPI5/DataLogging/dev/teensy_flash.log"
sleep 2
echo "Flash operation completed successfully" >> "/home/fbr-pi/software/Drybox/drybox/RPI5/DataLogging/dev/teensy_flash.log"
