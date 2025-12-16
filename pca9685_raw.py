# pca9685_raw.py
import time
import smbus

MODE1 = 0x00
PRESCALE = 0xFE

class PCA9685Raw:
    def __init__(self, address=0x40, bus_id=1, freq_hz=50):
        self.addr = address
        self.bus = smbus.SMBus(bus_id)
        self.set_pwm_freq(freq_hz)

    def _write(self, reg, val):
        self.bus.write_byte_data(self.addr, reg, val & 0xFF)

    def set_pwm_freq(self, freq_hz):
        # Based on datasheet: prescale = round(25MHz/(4096*freq)) - 1
        prescaleval = int(round(25000000.0 / (4096.0 * float(freq_hz)) - 1.0))

        oldmode = self.bus.read_byte_data(self.addr, MODE1)
        sleepmode = (oldmode & 0x7F) | 0x10  # sleep
        self._write(MODE1, sleepmode)
        self._write(PRESCALE, prescaleval)
        self._write(MODE1, oldmode)
        time.sleep(0.005)
        self._write(MODE1, oldmode | 0x80)  # restart
        time.sleep(0.005)

    def set_pwm(self, channel, on, off):
        base = 0x06 + 4 * int(channel)
        self._write(base + 0, on & 0xFF)
        self._write(base + 1, (on >> 8) & 0xFF)
        self._write(base + 2, off & 0xFF)
        self._write(base + 3, (off >> 8) & 0xFF)

    def set_pwm_off(self, channel, off):
        self.set_pwm(channel, 0, int(off))

