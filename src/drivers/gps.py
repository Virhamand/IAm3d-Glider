"""
GPS driver for the glider telemetry system.

Reads NMEA messages from the M10 GPS receiver over the
Raspberry Pi UART and extracts basic position information.
"""

import serial
import pynmea2


class GPS:
    """Interface for reading GPS data over UART."""

    def __init__(self, port="/dev/serial0", baudrate=9600):
        # Open the Raspberry Pi UART connected to the GPS TX pin.
        self.serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=1
        )

    def read(self):
        """
        Read one UART message from the GPS.

        Returns:
            dict: GPS position/fix information when a valid
                  GGA message is received.
            None: If no usable GPS message is available.
        """

        # Receive one NMEA sentence from the GPS.
        line = self.serial.readline().decode(
            "ascii",
            errors="ignore"
        ).strip()

        # NMEA messages should begin with '$'.
        if not line.startswith("$"):
            return None

        try:
            # Convert the raw NMEA sentence into a Python object.
            msg = pynmea2.parse(line)

            # GGA contains position, altitude, satellites,
            # and GPS fix information.
            if isinstance(msg, pynmea2.types.talker.GGA):
                return {
                    "latitude": msg.latitude,
                    "longitude": msg.longitude,
                    "altitude_m": float(msg.altitude or 0),
                    "satellites": int(msg.num_sats or 0),
                    "fix_quality": int(msg.gps_qual or 0)
                }

        except (pynmea2.ParseError, ValueError):
            # Ignore malformed/incomplete GPS messages.
            return None

        return None
