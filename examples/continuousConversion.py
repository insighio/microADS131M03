import utime

import ADS131M03


ADS_SCK_Pin = 4
ADS_MOSI_Pin = 6
ADS_MISO_Pin = 5
ADS_DRDY = 48


async def execute_task():
    # optional generation of PWM to provide clock to ADS131M03
    # p_CLKIN = Pin(7)
    # pwm = PWM(p_CLKIN, freq=2048000, duty_u16=32768)

    adc = ADS131M03.ADS131M03()
    adc.begin(ADS_SCK_Pin, ADS_MOSI_Pin, ADS_MISO_Pin, ADS_DRDY)

    # set 3 channels
    adc.set_input_channel_selection(0, 0)
    adc.set_input_channel_selection(1, 0)
    adc.set_input_channel_selection(2, 0)

    while True:
        print("Channel 1: {}, Channel 2: {}, Channel 3: {}".format(adc.read_adc()["ch0"], adc.read_adc()["ch1"], adc.read_adc()["ch2"]))
        utime.sleep_ms(1000)
