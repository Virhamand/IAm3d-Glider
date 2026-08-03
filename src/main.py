"""
Glider telemetry prototype.

Collects GPS position data from the M10 receiver and
magnetometer data from the IST8310 using a Raspberry Pi 4.

Current prototype:
    M10 GPS   -> UART
    IST8310   -> I2C

Future work:
    - Telemetry transmission
    - Data logging
    - Sensor validation
    - Compass calibration
    - Additional flight sensors
"""

import time

from drivers.gps import GPS
from drivers.compass import IST8310


def main():
    """Run the GPS/compass telemetry prototype."""

    # Initialize both sensors.
    gps = GPS()
    compass = IST8310()

    print("Starting glider telemetry...")

    while True:

        # Read the latest available GPS message.
        gps_data = gps.read()

        # Read the current magnetic-field measurement.
        compass_data = compass.read()

        # GPS data is only printed when a valid GGA
        # message has been received.
        if gps_data:
            print(
                "GPS | "
                f"Lat: {gps_data['latitude']:.6f} | "
                f"Lon: {gps_data['longitude']:.6f} | "
                f"Alt: {gps_data['altitude_m']:.1f} m | "
                f"Sats: {gps_data['satellites']} | "
                f"Fix: {gps_data['fix_quality']}"
            )

        # Display the current compass measurement.
        print(
            "COMPASS | "
            f"Heading: {compass_data['heading_deg']:.1f} deg | "
            f"X: {compass_data['mag_x']} | "
            f"Y: {compass_data['mag_y']} | "
            f"Z: {compass_data['mag_z']}"
        )

        # Prototype update rate of approximately 10 Hz.
        time.sleep(0.1)


if __name__ == "__main__":
    main()
