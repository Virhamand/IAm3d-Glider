# IAm3d-Glider
IAm3D Year 2 Glider

# Raspberry Pi Glider Telemetry

Wireless flight telemetry system using a Raspberry Pi 4 and MPU-6500 IMU.

## Features

- MPU-6500 communication over I2C
- 3-axis acceleration measurement
- 3-axis gyroscope measurement
- Gyroscope bias calibration
- Roll and pitch estimation
- Complementary filtering
- Timestamped onboard CSV logging
- UDP wireless telemetry
- Telemetry sequence numbers
- Ground-station CSV logging
- Packet-loss detection
- Live terminal telemetry dashboard
- Wireless signal-loss detection

## Architecture

MPU-6500
    |
    | I2C
    v
Raspberry Pi 4
    |
    | UDP / Wi-Fi
    v
Ground Station
    |
    +-- Live telemetry
    +-- CSV logging
    +-- Packet-loss monitoring

## Run

Start the ground station:

python3 ground_station/receiver.py

Then start telemetry on the Raspberry Pi:

python3 src/telemetry.py
