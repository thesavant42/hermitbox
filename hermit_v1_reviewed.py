# Hermit Box v.1 by savant42
# Pieced together from CircuitPython examples from Adafruit
# SPDX-FileCopyrightText: Copyright (c) 2022 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

import time
import board
import neopixel
import rainbowio
import usb_hid
import synthio
import digitalio
import audiomixer
import adafruit_lis3dh
from adafruit_tca8418 import TCA8418

toneMode = "BLUE"
toneMode_list = ["BEIGE", "RED", "BLUE"]

# My LED is GRB instead of RGB, so these color values may be wrong for you
RED = (0, 255, 0, 0)
BEIGE = (180, 255, 0, 0)
GREEN = (255, 0, 0, 0)
CYAN = (255, 0, 255, 0)
BLUE = (0, 0, 255, 0)
PURPLE = (0, 180, 255, 0)
BLACK = (0, 0, 0, 0)
WHITE = (255, 255, 255, 0)

# Keymap dictionary
keymap = {
    (4): (0, "1", 700, 900, 697, 1209),
    (3): (0, "2", 700, 1100, 697, 1336),
    (2): (0, "3", 900, 1100, 697, 1477),
    (1): (0, "A", 700, 1700, 697, 1633),
    (14): (0, "4", 700, 1300, 770, 1209),
    (13): (0, "5", 900, 1300, 770, 1336),
    (12): (0, "6", 1100, 1300, 770, 1477),
    (11): (0, "B", 900, 1700, 770, 1633),
    (24): (0, "7", 700, 1500, 852, 1209),
    (23): (0, "8", 900, 1500, 852, 1336),
    (22): (0, "9", 1100, 1500, 852, 1477),
    (21): (0, "C", 1100, 1700, 852, 1633),
    (34): (0, "*", 1300, 1700, 941, 1209),
    (33): (0, "0", 1300, 1500, 941, 1336),
    (32): (0, "#", 1100, 1700, 941, 1477),
    (31): (0, "D", 2600, 2600, 941, 1633),
}

# I2S Audio Setup
import audiobusio
power = digitalio.DigitalInOut(board.EXTERNAL_POWER)
power.switch_to_output(value=True)
audio = audiobusio.I2SOut(board.I2S_BIT_CLOCK, board.I2S_WORD_SELECT, board.I2S_DATA)

synth = synthio.Synthesizer(sample_rate=22050)
mixer = audiomixer.Mixer(voice_count=1, sample_rate=synth.sample_rate, channel_count=1, buffer_size=2048)
audio.play(mixer)
mixer.voice[0].play(synth)
mixer.voice[0].level = 0.05

# Neopixels Setup
OFF_COLOR = BLACK
neopixels = neopixel.NeoPixel(board.EXTERNAL_NEOPIXELS, 14, brightness=0.1)
neopixels.fill(OFF_COLOR)

i2c = board.I2C()
tca = TCA8418(i2c)
int1 = digitalio.DigitalInOut(board.ACCELEROMETER_INTERRUPT)

# Try to initialize LIS3DH safely
try:
    lis3dh = adafruit_lis3dh.LIS3DH_I2C(i2c, int1=int1)
except Exception as e:
    print(f"Error initializing LIS3DH: {e}")
    lis3dh = None

# Keypad Configuration
KEYPADPINS = (TCA8418.R0, TCA8418.R1, TCA8418.R2, TCA8418.R3, TCA8418.C0, TCA8418.C1, TCA8418.C2, TCA8418.C3)
for pin in KEYPADPINS:
    tca.keypad_mode[pin] = True
    tca.enable_int[pin] = True
    tca.event_mode_fifo[pin] = True

tca.key_intenable = True

# Main loop
print("Running! Mode is:", toneMode)
while True:
    if lis3dh and lis3dh.tapped:
        print("Double Tap! Changing modes!")
        if toneMode_list:
            toneMode = toneMode_list.pop(0)
            toneMode_list.append(toneMode)
        else:
            print("Error: toneMode_list is empty!")
        neopixels.fill(WHITE)
        time.sleep(0.1)
        neopixels.fill(OFF_COLOR)
        time.sleep(0.1)

    if tca.key_int:
        events = tca.events_count
        for _ in range(events):
            keyevent = tca.next_event
            keymap_number = (keyevent & 0x7F)
            if keymap_number in keymap:
                print(keymap[keymap_number][1])
                neopixels.fill(BLUE)
            else:
                print(f"Warning: Unknown key event {keymap_number}")
            time.sleep(0.05)  # Debounce keys
        tca.key_int = True  # Clear IRQ
        time.sleep(0.01)
