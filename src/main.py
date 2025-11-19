from machine import Pin
import time

led = Pin("LED", Pin.OUT)
print("Booted. Blinking...")

i = 0
while True:
    led.toggle()
    i += 1
    print(f"Tick {i}")
    time.sleep(1)