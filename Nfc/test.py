import time
import RPi.GPIO as GPIO
import psutil
from luma.core.interface.serial import i2c
from luma.oled.device import sh1106
from luma.core.render import canvas

# ==============================
# CONFIG
# ==============================

BUTTON_PIN = 17

RETURN_MODE_TIMEOUT = 20
INFO_MODE_TIMEOUT = 10
DOUBLE_CLICK_TIME = 0.5   # seconds window for double click

MODE_STATUS = "STATUS"
MODE_RETURN = "RETURN"
MODE_INFO = "INFO"

# Default book info shown in STATUS mode.
# TODO: Update these from your NFC / backend logic when a book is issued.
current_book_title = "No book issued"
current_submit_date = "--/--/----"

# ==============================
# OLED SETUP
# ==============================

serial = i2c(port=1, address=0x3C)
device = sh1106(serial)

# ==============================
# GPIO SETUP
# ==============================

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# ==============================
# SYSTEM INFO FUNCTIONS
# ==============================

def get_cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = float(f.read()) / 1000.0
        return f"{temp:.1f}C"
    except:
        return "N/A"

def get_cpu_usage():
    return f"{psutil.cpu_percent()}%"

def get_ram_usage():
    return f"{psutil.virtual_memory().percent}%"


# ==============================
# DRAW FUNCTIONS
# ==============================

def draw_status(book_title: str, submit_date: str):
    with canvas(device) as draw:
        draw.text((0, 0), "NFC SYSTEM", fill="white")
        draw.text((0, 18), "Mode: STATUS", fill="white")
        draw.text((0, 36), f"Book: {book_title}", fill="white")
        draw.text((0, 52), f"Submit: {submit_date}", fill="white")

def draw_return(countdown):
    with canvas(device) as draw:
        draw.text((0, 0), "RETURN MODE", fill="white")
        draw.text((0, 25), f"{countdown}s left", fill="white")

        bar_width = int((countdown / RETURN_MODE_TIMEOUT) * 128)
        draw.rectangle((0, 55, bar_width, 63), fill="white")

def draw_info():
    cpu = get_cpu_usage()
    ram = get_ram_usage()
    temp = get_cpu_temp()

    with canvas(device) as draw:
        draw.text((0, 0), "DEVICE INFO", fill="white")
        draw.text((0, 18), f"CPU:  {cpu}", fill="white")
        draw.text((0, 34), f"RAM:  {ram}", fill="white")
        draw.text((0, 50), f"TEMP: {temp}", fill="white")


# ==============================
# MAIN LOOP
# ==============================

current_mode = MODE_STATUS
mode_start_time = None

last_click_time = 0
click_timer_started = False
click_start_time = 0

print("Single click → RETURN")
print("Double click → INFO")

try:
    while True:
        now = time.time()

        # -----------------------------
        # BUTTON PRESS DETECTION
        # -----------------------------
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:

            press_time = time.time()

            # Wait for release (debounce)
            while GPIO.input(BUTTON_PIN) == GPIO.LOW:
                time.sleep(0.01)

            if press_time - last_click_time <= DOUBLE_CLICK_TIME:
                # DOUBLE CLICK
                current_mode = MODE_INFO
                mode_start_time = time.time()
                print("DOUBLE CLICK → INFO MODE")

                last_click_time = 0
                click_timer_started = False

            else:
                # First click
                last_click_time = press_time
                click_timer_started = True
                click_start_time = press_time

        # -----------------------------
        # SINGLE CLICK TIMEOUT CHECK
        # -----------------------------
        if click_timer_started:
            if time.time() - click_start_time > DOUBLE_CLICK_TIME:
                current_mode = MODE_RETURN
                mode_start_time = time.time()
                print("SINGLE CLICK → RETURN MODE")

                click_timer_started = False

        # -----------------------------
        # MODE HANDLING
        # -----------------------------
        if current_mode == MODE_RETURN:
            elapsed = int(now - mode_start_time)
            remaining = RETURN_MODE_TIMEOUT - elapsed

            if remaining <= 0:
                current_mode = MODE_STATUS
                print("Back to STATUS")
            else:
                draw_return(remaining)

        elif current_mode == MODE_INFO:
            elapsed = int(now - mode_start_time)

            if elapsed >= INFO_MODE_TIMEOUT:
                current_mode = MODE_STATUS
                print("Exit INFO")
            else:
                draw_info()

        else:
            # Default STATUS mode: show current issued book & submit date.
            # Replace the globals above from your NFC/backend logic.
            draw_status(current_book_title, current_submit_date)

        time.sleep(0.05)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    GPIO.cleanup()
