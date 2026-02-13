"""
Unified NFC daemon:
- Always-on PN532 NFC reader.
- Talks to backend /nfc/tap to issue/return books.
- Drives an SH1106 OLED and TWO buttons:
    - GPIO17 → RETURN mode (20s)
    - GPIO27 → INFO mode (10s)
"""

import os
import time
from datetime import datetime

import board
import busio
from adafruit_pn532.i2c import PN532_I2C

import RPi.GPIO as GPIO
import psutil
from luma.core.interface.serial import i2c
from luma.oled.device import sh1106
from luma.core.render import canvas

try:
    import requests
except ImportError:
    requests = None


# ==============================
# CONFIG
# ==============================

BUTTON_RETURN = 17
BUTTON_INFO = 27

RETURN_MODE_TIMEOUT = 20
INFO_MODE_TIMEOUT = 10

MODE_STATUS = "STATUS"
MODE_RETURN = "RETURN"
MODE_INFO = "INFO"

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")
NFC_TAP_URL = f"{BACKEND_URL}/nfc/tap"
NFC_STATUS_URL = f"{BACKEND_URL}/nfc/status"
NFC_SCAN_URL = f"{BACKEND_URL}/nfc/scan"

SAME_TAG_COOLDOWN_SECONDS = 0.8


# ==============================
# STATE
# ==============================

current_mode = MODE_STATUS
mode_start_time = None

last_uid = None
last_uid_time = None

current_book_title = "No book issued"
current_submit_date = "--/--/----"
status_line = "Tap book"

frame_counter = 0


# ==============================
# OLED SETUP
# ==============================

serial = i2c(port=1, address=0x3C)
device = sh1106(serial)


# ==============================
# GPIO SETUP
# ==============================

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_RETURN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON_INFO, GPIO.IN, pull_up_down=GPIO.PUD_UP)


# ==============================
# SYSTEM INFO
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


def format_date(iso_str):
    if not iso_str:
        return "--/--/----"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except:
        return "--/--/----"


# ==============================
# DRAW FUNCTIONS
# ==============================

def draw_status(title, date, message, tick):
    spinner = ["-", "\\", "|", "/"]
    spin = spinner[tick % 4]
    with canvas(device) as draw:
        draw.text((0, 0), f"{spin} NFC SYSTEM", fill="white")
        draw.text((0, 18), message[:20], fill="white")
        draw.text((0, 36), f"Book: {title[:16]}", fill="white")
        draw.text((0, 52), f"Submit: {date}", fill="white")


def draw_return(countdown):
    with canvas(device) as draw:
        draw.text((0, 0), "ISSUE/RETURN MODE", fill="white")
        draw.text((0, 24), f"{countdown}s left", fill="white")
        bar = int((countdown / RETURN_MODE_TIMEOUT) * 128)
        draw.rectangle((0, 55, bar, 63), fill="white")


def draw_info():
    with canvas(device) as draw:
        draw.text((0, 0), "DEVICE INFO", fill="white")
        draw.text((0, 18), f"CPU:  {get_cpu_usage()}", fill="white")
        draw.text((0, 34), f"RAM:  {get_ram_usage()}", fill="white")
        draw.text((0, 50), f"TEMP: {get_cpu_temp()}", fill="white")


def draw_error(msg):
    with canvas(device) as draw:
        draw.text((0, 0), "NFC ERROR", fill="white")
        draw.text((0, 20), msg[:20], fill="white")


# ==============================
# BACKEND COMMUNICATION
# ==============================

def send_scan(uid_hex):
    if not requests:
        return
    try:
        requests.post(NFC_SCAN_URL, json={"nfc_tag_id": uid_hex}, timeout=5)
    except:
        pass


def query_status(uid_hex):
    global current_book_title, current_submit_date, status_line

    if not requests:
        return

    try:
        r = requests.post(NFC_STATUS_URL, json={"nfc_tag_id": uid_hex}, timeout=5)
        data = r.json()
    except:
        status_line = "Network error"
        return

    if r.status_code != 200:
        status_line = "Error"
        return

    current_book_title = data.get("book_name", "Unknown")
    current_submit_date = format_date(data.get("due_date"))
    status_line = data.get("message", "Available")[:20]


def send_tap(uid_hex):
    global current_book_title, current_submit_date, status_line, current_mode
    global last_uid

    if not requests:
        return

    try:
        r = requests.post(NFC_TAP_URL, json={"nfc_tag_id": uid_hex}, timeout=5)
    except requests.exceptions.RequestException:
        status_line = "Network error"
        current_mode = MODE_STATUS
        last_uid = None
        return

    try:
        data = r.json()
    except:
        data = {}

    if r.status_code == 200:
        action = data.get("action")
        book = data.get("book_name", "Unknown")

        if action == "issue":
            current_book_title = book
            current_submit_date = format_date(data.get("due_date"))
            status_line = "Book Issued"

        elif action == "return":
            current_book_title = "No book issued"
            current_submit_date = "--/--/----"
            status_line = "Book Returned"

        else:
            status_line = data.get("message", "Done")[:20]

        current_mode = MODE_STATUS
        last_uid = None
        return

    else:
        backend_msg = data.get("detail") or data.get("message") or "Book Returned"
        status_line = backend_msg[:20]
        current_mode = MODE_STATUS
        last_uid = None
        return


# ==============================
# MAIN LOOP
# ==============================

def main():
    global current_mode, mode_start_time
    global last_uid, last_uid_time
    global frame_counter
    global status_line

    i2c_bus = busio.I2C(board.SCL, board.SDA)
    pn532 = PN532_I2C(i2c_bus)
    pn532.SAM_configuration()

    print("NFC daemon started")

    try:
        while True:

            # BUTTONS
            if GPIO.input(BUTTON_RETURN) == GPIO.LOW:
                time.sleep(0.05)
                if GPIO.input(BUTTON_RETURN) == GPIO.LOW:
                    current_mode = MODE_RETURN
                    mode_start_time = time.time()
                    while GPIO.input(BUTTON_RETURN) == GPIO.LOW:
                        time.sleep(0.01)

            if GPIO.input(BUTTON_INFO) == GPIO.LOW:
                time.sleep(0.05)
                if GPIO.input(BUTTON_INFO) == GPIO.LOW:
                    current_mode = MODE_INFO
                    mode_start_time = time.time()
                    while GPIO.input(BUTTON_INFO) == GPIO.LOW:
                        time.sleep(0.01)

            # NFC
            uid = pn532.read_passive_target(timeout=0.2)
            if uid:
                now_uid = time.time()
                if uid != last_uid or (now_uid - (last_uid_time or 0)) > SAME_TAG_COOLDOWN_SECONDS:
                    uid_hex = "".join(format(b, "02X") for b in uid)
                    print("UID:", uid_hex)

                    send_scan(uid_hex)

                    if current_mode == MODE_RETURN:
                        status_line = "Processing..."
                        send_tap(uid_hex)
                    else:
                        status_line = "Checking..."
                        query_status(uid_hex)

                    last_uid = uid
                    last_uid_time = now_uid

            # DISPLAY
            if current_mode == MODE_RETURN:
                elapsed = int(time.time() - mode_start_time)
                remaining = RETURN_MODE_TIMEOUT - elapsed
                if remaining <= 0:
                    current_mode = MODE_STATUS
                else:
                    draw_return(remaining)

            elif current_mode == MODE_INFO:
                elapsed = int(time.time() - mode_start_time)
                if elapsed >= INFO_MODE_TIMEOUT:
                    current_mode = MODE_STATUS
                else:
                    draw_info()

            else:
                draw_status(current_book_title, current_submit_date, status_line, frame_counter)
                frame_counter += 1

            time.sleep(0.08)

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        GPIO.cleanup()


if __name__ == "__main__":
    main()
