#!/bin/bash

# Activate the virtual environment located in your home folder
# Replace 'path/to/venv' with your actual path
source /home/fabriusa/db2/bin/activate

# Move to the directory where your project lives
cd /home/fabriusa/dry_box_temp/RPI5/Python

# Execute your python script
/home/fabriusa/db2/bin/python logDB.py
/home/fabriusa/db2/bin/python serial_to_log.py
