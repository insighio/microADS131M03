from machine import SoftSPI, Pin

# from time import sleep_us

CONSTANT = 1.2 / 2**23


class ADS131M03:
    def __init__(self):
        self.spi = None
        self.drdy_pin = None
        self.dummy_byte_array_9 = bytearray([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        self.dummy_byte_array_12 = bytearray([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        self.pow2_8 = pow(2, 8)

    def begin(self, ADS_SCK_Pin, ADS_MOSI_Pin, ADS_MISO_Pin, ADS_DRDY):

        self.drdy_pin = Pin(ADS_DRDY, Pin.IN)
        self.spi = SoftSPI(
            baudrate=2048000,
            polarity=0,
            phase=1,
            bits=8,
            firstbit=SoftSPI.MSB,
            sck=Pin(ADS_SCK_Pin),
            mosi=Pin(ADS_MOSI_Pin),
            miso=Pin(ADS_MISO_Pin),
        )

    def write_register(self, address, value):
        cmd = 0x6000 | (address << 7)
        self.spi.write(bytearray([cmd >> 8, cmd & 0xFF, 0x00]))
        self.spi.write(bytearray([value >> 8, value & 0xFF, 0x00]))
        self.spi.write(self.dummy_byte_array_9)
        response = bytearray(15)
        self.spi.readinto(response, 0x00)

    def write_register_masked(self, address, value, mask):
        current_value = self.read_register(address)
        new_value = (current_value & ~mask) | (value & mask)
        self.write_register(address, new_value)

    def read_register(self, address):
        cmd = 0xA000 | (address << 7)
        self.spi.write(bytearray([cmd >> 8, cmd & 0xFF, 0x00]))
        self.spi.write(self.dummy_byte_array_12)
        response = bytearray(15)
        self.spi.readinto(response, 0x00)
        return (response[0] << 8) | response[1]

    def is_data_ready(self):
        return self.drdy_pin.value() == 0

    def read_adc(self):
        raw_data = bytearray(15)
        self.spi.readinto(raw_data, 0x00)

        res = {
            "status": (raw_data[0] << 8) | raw_data[1],
            "ch0": self._convert_data(raw_data[3:6]),
            "ch1": self._convert_data(raw_data[6:9]),
            "ch2": self._convert_data(raw_data[9:12]),
        }
        return res

    def _convert_data(self, data):
        value = ((data[0] << 16) | (data[1] << 8) | data[2]) & 0x00FFFFFF
        if value & 0x800000:  # Check if negative
            value = -((~value & 0xFFFFFF) + 1)
        return self.twoCompDeco(value) * CONSTANT

    def set_power_mode(self, power_mode):
        if power_mode > 3:
            return False
        self.write_register_masked(0x03, power_mode, 0x0003)
        return True

    def set_channel_enable(self, channel, enable):
        if channel > 3:
            return False
        self.write_register_masked(0x03, enable << (8 + channel), 1 << (8 + channel))
        return True

    def set_channel_pga(self, channel, pga):
        if channel > 3:
            return False
        self.write_register_masked(0x04, pga << (channel * 4), 0x7 << (channel * 4))
        return True

    def set_input_channel_selection(self, channel, input_mux):
        if channel > 3:
            return False
        self.write_register_masked(0x09 + channel * 5, input_mux, 0x0003)
        return True

    def set_channel_offset_calibration(self, channel, offset):
        if channel > 3:
            return False
        msb = (offset >> 8) & 0xFFFF
        lsb = offset & 0xFF
        self.write_register(0x0A + channel * 5, msb)
        self.write_register_masked(0x0B + channel * 5, lsb << 8, 0xFF00)
        return True

    def set_channel_gain_calibration(self, channel, gain):
        if channel > 3:
            return False
        msb = (gain >> 8) & 0xFFFF
        lsb = gain & 0xFF
        self.write_register(0x0C + channel * 5, msb)
        self.write_register_masked(0x0D + channel * 5, lsb << 8, 0xFF00)
        return True

    def twoCompDeco(self, data):
        data <<= 8
        return data / self.pow2_8
