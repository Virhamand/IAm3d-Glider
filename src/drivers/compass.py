"""
IST8310 magnetometer driver for the glider telemetry system.

Communicates with the IST8310 over the Raspberry Pi I2C bus
and reads the X, Y, and Z magnetic-field measurements.
"""

import math
import time

from smbus2 import SMBus


class IST8310:
    """Basic I2C interface for the IST8310 magnetometer."""

    ADDRESS = 0x0E

    # IST8310 register addresses.
    REG_WHO_AM_I = 0x00
    REG_DATA = 0x03
    REG_CONTROL = 0x0A

    def __init__(self, bus=1):
        # Raspberry Pi normally exposes I2C devices on bus 1.
        self.bus = SMBus(bus)

    def who_am_i(self):
        """Read the device identification register."""

        return self.bus.read_byte_data(
            self.ADDRESS,
            self.REG_WHO_AM_I
        )

    def read(self):
        """
        Take one magnetometer measurement.

        Returns:
            dict containing raw X/Y/Z measurements and a
            preliminary 2-D heading estimate.
        """

        # Request a single magnetometer measurement.
        self.bus.write_byte_data(
            self.ADDRESS,
            self.REG_CONTROL,
            0x01
        )

        # Give the sensor time to complete the measurement.
        time.sleep(0.01)

        # Read six bytes:
        # XL, XH, YL, YH, ZL, ZH.
        data = self.bus.read_i2c_block_data(
            self.ADDRESS,
            self.REG_DATA,
            6
        )

        x = self._signed16(data[0], data[1])
        y = self._signed16(data[2], data[3])
        z = self._signed16(data[4], data[5])

        # Preliminary heading using the X/Y magnetic field.
        # Calibration and tilt compensation can be added later.
        heading = math.degrees(math.atan2(y, x))

        if heading < 0:
            heading += 360

        return {
            "mag_x": x,
            "mag_y": y,
            "mag_z": z,
            "heading_deg": heading
        }

    @staticmethod
    def _signed16(low_byte, high_byte):
        """Combine two bytes into a signed 16-bit integer."""

        value = (high_byte << 8) | low_byte

        if value >= 32768:
            value -= 65536

        return value
