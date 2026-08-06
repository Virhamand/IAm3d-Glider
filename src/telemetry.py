import time
import csv
import math

from drivers.mpu6500 import MPU6500
from telemetry_packet import create_packet
from udp_sender import UDPSender


# -----------------------------
# Settings
# -----------------------------

# Change to your ground station IP
GROUND_IP = "192.168.137.1"

GROUND_PORT = 5005

# Complementary filter setting
ALPHA = 0.98

# About 10 Hz
SAMPLE_DELAY = 0.1


# -----------------------------
# Setup
# -----------------------------

# Create IMU
imu = MPU6500()

# Calibrate gyro
imu.calibrate_gyro()

# Create UDP sender
sender = UDPSender(
    GROUND_IP,
    GROUND_PORT
)

# Open onboard telemetry log
file = open(
    "flight_data.csv",
    "w",
    newline=""
)

writer = csv.writer(file)

# Write CSV column names
writer.writerow([
    "sequence",
    "time_s",
    "ax_g",
    "ay_g",
    "az_g",
    "gx_dps",
    "gy_dps",
    "gz_dps",
    "roll_deg",
    "pitch_deg"
])


# -----------------------------
# Starting values
# -----------------------------

sequence = 0

# Read starting acceleration
ax, ay, az = imu.read_accel()

# Calculate starting roll
filtered_roll = math.degrees(
    math.atan2(
        ay,
        math.sqrt(ax * ax + az * az)
    )
)

# Calculate starting pitch
filtered_pitch = math.degrees(
    math.atan2(
        -ax,
        math.sqrt(ay * ay + az * az)
    )
)

# Save timing information
start_time = time.monotonic()
previous_time = start_time


# -----------------------------
# Main telemetry loop
# -----------------------------

try:

    print("Telemetry started.")

    while True:

        # Read accelerometer
        ax, ay, az = imu.read_accel()

        # Read gyroscope
        gx, gy, gz = imu.read_gyro()


        # Get current time
        current_time = time.monotonic()

        # Time since last measurement
        dt = current_time - previous_time
        previous_time = current_time

        # Time since program started
        elapsed_time = current_time - start_time


        # Calculate roll from accelerometer
        accel_roll = math.degrees(
            math.atan2(
                ay,
                math.sqrt(ax * ax + az * az)
            )
        )

        # Calculate pitch from accelerometer
        accel_pitch = math.degrees(
            math.atan2(
                -ax,
                math.sqrt(ay * ay + az * az)
            )
        )


        # Filter roll
        filtered_roll = (
            ALPHA
            * (filtered_roll + gx * dt)
            + (1 - ALPHA) * accel_roll
        )

        # Filter pitch
        filtered_pitch = (
            ALPHA
            * (filtered_pitch + gy * dt)
            + (1 - ALPHA) * accel_pitch
        )


        # Save onboard data
        writer.writerow([
            sequence,
            elapsed_time,
            ax,
            ay,
            az,
            gx,
            gy,
            gz,
            filtered_roll,
            filtered_pitch
        ])


        # Create telemetry packet
        packet = create_packet(
            sequence,
            elapsed_time,
            ax,
            ay,
            az,
            gx,
            gy,
            gz,
            filtered_roll,
            filtered_pitch
        )


        # Send to ground station
        sender.send(packet)


        # Print telemetry
        print(
            f"Seq: {sequence} | "
            f"Roll: {filtered_roll:.2f} deg | "
            f"Pitch: {filtered_pitch:.2f} deg"
        )


        # Next packet
        sequence += 1

        # About 10 Hz
        time.sleep(SAMPLE_DELAY)


except KeyboardInterrupt:

    print("\nStopping telemetry...")


finally:

    # Close everything
    file.close()
    sender.close()
    imu.close()

    print("Flight data saved.")
