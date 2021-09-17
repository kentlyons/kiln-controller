"""
max6675.py

Class which defines interaction with the MAX6675 sensor.

Copyright (c) 2021 Kent Lyons
Copyright (c) 2019 John Robinson
Copyright (c) 2015 Troy Dack

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""
import logging
import warnings

import Adafruit_GPIO as Adafruit_GPIO
import Adafruit_GPIO.SPI as SPI


class MAX6675(object):
    """Class to represent an MAX6675 thermocouple temperature measurement board.
    """


    def __init__(self, cs, clk, do, units="c", spi=None, gpio=None):
        """Initialize MAX6675 device with software SPI on the specified CLK,
	CS, and DO pins.  Alternatively can specify hardware SPI by sending an
	Adafruit_GPIO.SPI.SpiDev device in the spi parameter.
	"""
        self._logger = logging.getLogger('Adafruit_MAX6675.MAX6675')
        self._spi = None
        self.noConnection = self.shortToGround = self.shortToVCC = self.unknownError = False

        # Handle hardware SPI
        if spi is not None:
           self._logger.debug('Using hardware SPI')
           self._spi = spi
        elif clk is not None and cs is not None and do is not None:
            self._logger.debug('Using software SPI')
            # Default to platform GPIO if not provided.
            if gpio is None:
                gpio = Adafruit_GPIO.get_platform_gpio()
            self._spi = SPI.BitBang(gpio, clk, None, do, cs)
        else:
            raise ValueError(
                'Must specify either spi for for hardware SPI or clk, cs, and do for softwrare SPI!')
        self._spi.set_clock_hz(5000000)
        self._spi.set_mode(0)
        self._spi.set_bit_order(SPI.MSBFIRST)
        self.units = units


    def read_temp_c(self):
        """
        Return the thermocouple temperature value in degrees celsius.
        """
        self.noConnection = False
        v = self._read16()
        # Check for error reading value.
        if v & 0x4:
            self.noConnection = True
            return float('NaN')
        # Check if signed bit is set.
        if v & 0x80000000:
            # Negative value, take 2's compliment. Compute this with subtraction
            # because python is a little odd about handling signed/unsigned.
            v >>= 3 # only need the 12 MSB
            v -= 4096
        else:
            # Positive value, just shift the bits to get the value.
            v >>= 3 # only need the 12 MSB
        # Scale by 0.25 degrees C per bit and return value.
        temp_c = v * 0.25

        self._logger.debug("Thermocouple Temperature {0} deg. C".format(temp_c))

        return temp_c

    def _read16(self):
        # Read 16 bits from the SPI bus.
        raw = self._spi.read(2)
        if raw is None or len(raw) != 2:
            raise RuntimeError('Did not read expected number of bytes from device!')
        value = raw[0] << 8 | raw[1]
        self._logger.debug('Raw value: 0x{0:08X}'.format(value & 0xFFFFFFFF))
        return value

    # added by jbruce to mimic MAX31855 lib
    def to_c(self, celsius):
        '''Celsius passthrough for generic to_* method.'''
        return celsius

    def to_k(self, celsius):
        '''Convert celsius to kelvin.'''
        return celsius + 273.15

    def to_f(self, celsius):
        '''Convert celsius to fahrenheit.'''
        return celsius * 9.0/5.0 + 32

    def checkErrors(self):
        pass

    def get(self):
        self.checkErrors()
        celcius = self.read_temp_c()
        return getattr(self, "to_" + self.units)(celcius)


