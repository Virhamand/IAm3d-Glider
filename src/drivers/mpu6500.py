from smbus2 import SMBus
import time


class MPU6500:

    def __init__(self, bus_number=1, address=0x68):

        # I2C settings
        self.bus = SMBus(bus_number)
        self.address = address

        # Sensor registers
        self.PWR_MGMT_1 = 0x6B

        self.ACCEL_XOUT_H = 0x3B
        self.ACCEL_YOUT_H = 0x3D
        self.ACCEL_ZOUT_H = 0x3F

        self.GYRO_XOUT_H = 0x43
        self.GYRO_YOUT_H = 0x45
        self.GYRO_ZOUT_H = 0x47

        # Gyro calibration values
        self.gx_bias = 0.0
        self.gy_bias = 0.0
        self.gz_bias = 0.0

        # Wake up sensor
        self.bus.write_byte_data(
            self.address,
            self.PWR_MGMT_1,
            0x00
        )


    def read_word(self, register):

        # Read two bytes
        high = self.bus.read_byte_data(
            self.address,
            register
        )

        low = self.bus.read_byte_data(
            self.address,
            register + 1
        )

        # Combine bytes
        value = (high << 8) | low

        # Convert to signed value
        if value >= 32768:
            value -= 65536

        return value


    def read_accel(self):

        # Read raw acceleration
        ax = self.read_word(self.ACCEL_XOUT_H)
        ay = self.read_word(self.ACCEL_YOUT_H)
        az = self.read_word(self.ACCEL_ZOUT_H)

        # Convert to g
        ax /= 16384.0
        ay /= 16384.0
        az /= 16384.0

        return ax, ay, az


    def read_gyro(self):

        # Read raw gyro
        gx = self.read_word(self.GYRO_XOUT_H)
        gy = self.read_word(self.GYRO_YOUT_H)
        gz = self.read_word(self.GYRO_ZOUT_H)

        # Convert to degrees/second
        gx = gx / 131.0 - self.gx_bias
        gy = gy / 131.0 - self.gy_bias
        gz = gz / 131.0 - self.gz_bias

        return gx, gy, gz


    def calibrate_gyro(self, samples=500):

        print("Keep MPU-6500 still...")

        gx_sum = 0.0
        gy_sum = 0.0
        gz_sum = 0.0

        for _ in range(samples):

            # Read gyro
            gx = self.read_word(self.GYRO_XOUT_H) / 131.0
            gy = self.read_word(self.GYRO_YOUT_H) / 131.0
            gz = self.read_word(self.GYRO_ZOUT_H) / 131.0

            # Add readings
            gx_sum += gx
            gy_sum += gy
            gz_sum += gz

            time.sleep(0.01)

        # Calculate average bias
        self.gx_bias = gx_sum / samples
        self.gy_bias = gy_sum / samples
        self.gz_bias = gz_sum / samples

        print("Calibration complete!")

        print(
            f"Bias: "
            f"{self.gx_bias:.2f}, "
            f"{self.gy_bias:.2f}, "
            f"{self.gz_bias:.2f} deg/s"
        )


    def close(self):

        # Close I2C bus
        self.bus.close()
