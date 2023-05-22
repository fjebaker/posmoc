import logging
import sys
import struct
import asyncio
import time
import random

import crc
import serial

import numpy as np


EYE_PAN_RIGHT = 130
EYE_PAN_LEFT = 55

EYE_TILT_DOWN = 180
EYE_TILT_UP = 100

JAW_OPEN = 120
JAW_CLOSED = 80

NECK_LEFT = 0
NECK_RIGHT = 80

# order is
# jaw, neck, eyepan, eyetilt
# eye left, eye right

# returns
# * == good
# + == reset
# - == checksum fail

logger = logging.getLogger(__name__)


def rescale(x, xmin, xmax):
    x = min(100, x)
    x = max(0, x)
    return int((x / 100) * (xmax - xmin) + xmin)


class HeadControl:
    def __init__(self, device: str):
        self.serial = serial.Serial(device, 9600)
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()

        self.crc = crc.Calculator(crc.Crc8.CCITT)

        self.values = {
            "jaw": 0,
            "head": 50,
            "eyepan": 50,
            "eyetilt": 50,
            "lefteye": 0b100,
            "righteye": 0b100,
        }

        self.speaking = False

    async def start_idle(self):
        while True:
            logger.debug("idling...")
            await asyncio.sleep(random.random() * 2.0 + 3.0)

            if self.speaking:
                # if we're speaking we just update values
                self.values["lefteye"] = 0
                self.values["righteye"] = 0

                await asyncio.sleep(0.11)
                
                # always blue i suppose
                self.values["lefteye"] = 0b100
                self.values["righteye"] = 0b100
            else:
                self._write_from_kwargs(lefteye=0, righteye=0)
                time.sleep(0.1)
                self._write_from_kwargs()

    async def set_thinking(self):
        i = 0
        while True:
            await asyncio.sleep(random.random() * 2.0 + 3.0)
            if i % 2 == 0:
                # look down and right
                self._write_from_kwargs(eyepan=0, eyetilt=100)
            else:
                self._write_from_kwargs(eyepan=100, eyetilt=100)
            i += 1

    def _write(self, values: list):
        # send header
        for i in range(7):
            self.serial.write((42).to_bytes(1, "little"))

        logger.debug("writing: %s", values)
        for v in values:
            self.serial.write(v.to_bytes(1, "little"))

        checksum = self.crc.checksum(bytes(values))
        logger.debug("checksum: %d", checksum)

        self.serial.write(checksum.to_bytes(1, "little"))

    def write(self, **kwargs):
        # update values
        self.values = self._write_from_kwargs(**kwargs)

    def _write_from_kwargs(self, **kwargs):
        values = dict(self.values, **kwargs)
        adjusted = [
            rescale(values["jaw"], JAW_CLOSED, JAW_OPEN),
            rescale(values["head"], NECK_LEFT, NECK_RIGHT),
            rescale(values["eyepan"], EYE_PAN_LEFT, EYE_PAN_RIGHT),
            rescale(values["eyetilt"], EYE_TILT_UP, EYE_TILT_DOWN),
            values["lefteye"],
            values["righteye"],
        ]

        self._write(adjusted)
        return values
