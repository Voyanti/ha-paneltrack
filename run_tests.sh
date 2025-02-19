#!/bin/bash

echo "TESTS Add src to PYTHONPATH"
echo ""
export PYTHONPATH=src/

echo "TESTS Start Mosquitto in the background"
echo ""
mosquitto -p 1884 -d
MOSQUITTO_PID=$!

echo "TESTS Run unittests"
echo ""
python3 -m unittest -v

echo "TESTS Stop Mosquitto"
echo ""
kill $MOSQUITTO_PID
