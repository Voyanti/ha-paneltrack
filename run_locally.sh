#!/bin/bash
echo ""

echo "LOCAL Start Mosquitto in the background"
echo ""
mosquitto -p 1884 -d
# MOSQUITTO_PID=$!

echo "Hello Paneltrack"
echo "---"

python3 -m src.app config.yaml

echo "sleep 3s"
sleep 3

echo "LOCAL Stop Mosquitto"
echo ""
kill $(pgrep -f "mosquitto -p 1884")