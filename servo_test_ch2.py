import time
import smbus

bus = smbus.SMBus(1)
ADDR = 0x40

def write(reg, val):
    bus.write_byte_data(ADDR, reg, val)

def set_pwm(ch, off):
    base = 0x06 + 4 * ch
    write(base, 0)
    write(base + 1, 0)
    write(base + 2, off & 0xFF)
    write(base + 3, off >> 8)

# init 50Hz
write(0x00, 0x10)
write(0xFE, 121)
write(0x00, 0x80)
time.sleep(0.1)

print("Set ch2 to 300")
set_pwm(2, 300)
time.sleep(2)

print("Set ch2 to 450")
set_pwm(2, 450)
time.sleep(2)

print("Done")

