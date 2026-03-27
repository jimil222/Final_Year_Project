import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.cleanup()  # Force clean slate

GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print("After cleanup + setup:")
for _ in range(5):
    print(f"GPIO17: {GPIO.input(17)} | GPIO27: {GPIO.input(27)}")
    time.sleep(0.3)

GPIO.cleanup()