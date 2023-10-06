# Hermit Box v.1 by savant42
# Pieced together from  CircuitPython examples from Adafruit
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

# My LED is GRB instead of RGB, so these color values will likely be wrong for you
#RED = (255, 0, 0, 0) # Looks green to me
RED = (0, 255, 0, 0)
BEIGE = (180, 255, 0, 0)
GREEN = (255, 0, 0, 0)
CYAN = (255, 0, 255, 0)
BLUE = (0, 0, 255, 0)
PURPLE = (0, 180, 255, 0)
BLACK = (0, 0, 0, 0)
WHITE = (255, 255, 255, 0)

## JB Keymap (key_event) : (layer, "Key", MFLOW, MFHIGH, DTMFLOW, DTMFHIGH),
# I don't use the layer number column in this code, but I may use it later to toggle modes on boot
#
# 4x4 Matrix Keypad, Begins Top left with key "1", left to right, row by row
keymap = {
            (4) : (0, "1", 700, 900, 697, 1209),   # 1
            (3) : (0, "2", 700, 1100, 697, 1336),  # 2
            (2) : (0, "3", 900, 1100, 697, 1477),  # 3
            (1) : (0, "A", 700, 1700, 697, 1633),  # "ST3" / "A"
            (14) : (0, "4", 700, 1300, 770, 1209), # 4
            (13) : (0, "5", 900, 1300, 770, 1336), # 5
            (12) : (0, "6", 1100, 1300, 770, 1477),# 6
            (11) : (0, "B", 900, 1700, 770, 1633), # "ST2" / "B"
            (24) : (0, "7", 700, 1500, 852, 1209), # 7
            (23) : (0, "8", 900, 1500, 852, 1336), # 8
            (22) : (0, "9", 1100, 1500, 852, 1477), # 9
            (21) : (0, "C", 1100, 1700, 852, 1633), # KP
            (34) : (0, "*", 1300, 1700, 941, 1209), # KP2
            (33) : (0, "0", 1300, 1500, 941, 1336), # 0 / 10
            (32) : (0, "#", 1100, 1700, 941, 1477), # "ST" / #
            (31) : (0, "D", 2600, 2600, 941, 1633)  # 2600hz / "D"
}

# for I2S audio with external I2S DAC board
import audiobusio
# I2S audio on PropMaker Feather RP2040
power = digitalio.DigitalInOut(board.EXTERNAL_POWER)
power.switch_to_output(value=True)
audio = audiobusio.I2SOut(board.I2S_BIT_CLOCK, board.I2S_WORD_SELECT, board.I2S_DATA)

synth = synthio.Synthesizer(sample_rate=22050) # reduced sample rate to reduce (hopefully) audio glitches
mixer = audiomixer.Mixer(voice_count=1, sample_rate=synth.sample_rate, channel_count=1, buffer_size=2048)

audio.play(mixer)
mixer.voice[0].play(synth)
mixer.voice[0].level = 0.05 # Float, from 0 to 1. 0.05 = Much more reasonable volume.

# Neopixels
OFF_COLOR = (BLACK)
neopixels = neopixel.NeoPixel(board.EXTERNAL_NEOPIXELS, 14, brightness=0.1)
neopixels.fill(OFF_COLOR)

i2c = board.I2C()  # uses board.SCL and board.SDA
tca = TCA8418(i2c)
int1 = digitalio.DigitalInOut(board.ACCELEROMETER_INTERRUPT)  # Set this to the correct pin for the interrupt!

# set up all R0-R4 pins and C0-C3 pins as keypads
KEYPADPINS = (
    TCA8418.R0,
    TCA8418.R1,
    TCA8418.R2,
    TCA8418.R3,
    TCA8418.C0,
    TCA8418.C1,
    TCA8418.C2,
    TCA8418.C3,
)

# make them inputs with pullups
for pin in KEYPADPINS:
    tca.keypad_mode[pin] = True
    # make sure the key pins generate FIFO events
    tca.enable_int[pin] = True
    # we will stick events into the FIFO queue
    tca.event_mode_fifo[pin] = True

# turn on INT output pin
tca.key_intenable = True

lis3dh = adafruit_lis3dh.LIS3DH_I2C(i2c, int1=int1)

# Main loop
print("Running! Mode is:", toneMode)
while True:
    #print("Tone Mode:", toneMode)
    lis3dh.set_tap(2, 100, time_limit = 3)
    if lis3dh.tapped:
        print("Double Tap! Changing modes!")
        toneMode = toneMode_list.pop(0)
        toneMode_list.append(toneMode)
        print("Mode is now:", toneMode)
        # Double blink led in confirmation of mode change
        neopixels.fill(WHITE)
        time.sleep(.1)
        neopixels.fill(OFF_COLOR)
        time.sleep(.1)
        neopixels.fill(WHITE)
        time.sleep(.1)
        neopixels.fill(OFF_COLOR)

    if tca.key_int:
        # first figure out how big the queue is
        events = tca.events_count
        # now print each event in the queue
        for _ in range(events):
            keyevent = tca.next_event
            keymap_number = (keyevent & 0x7F)
            #print(
            #    "\tKey event: 0x%02X - key #%d " % (keyevent, keyevent & 0x7F), end=""
            #)
            if keyevent & 0x80:  # if key is pressed
                    print(keymap[keymap_number][1])
                    if toneMode == "BLUE":
                        ON_COLOR = (BLUE)
                        lownote1 = synthio.Note(keymap[keymap_number][2])
                        hinote1 = synthio.Note(keymap[keymap_number][3])
                    elif toneMode == "BEIGE":
                        ON_COLOR = (BEIGE)
                        lownote1 = synthio.Note(keymap[keymap_number][4])
                        hinote1 = synthio.Note(keymap[keymap_number][5])
                    elif toneMode == "RED":
                        ON_COLOR = (RED)
                        lownote1 = synthio.Note(1700)
                        hinote1 = synthio.Note(2200)
                    #print("Low tone info:", lownote1)
                    #print("High tone info:", hinote1)
                    neopixels.fill(ON_COLOR)
                    synth.press((lownote1, hinote1))
            else:
                neopixels.fill(OFF_COLOR)
                synth.release_all()
        tca.key_int = True  # clear the IRQ by writing 1 to it
        time.sleep(0.01)
