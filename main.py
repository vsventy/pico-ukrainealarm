import json
import network
import urequests
from utime import sleep
from machine import Pin, I2C
from machine_i2c_lcd import I2cLcd

from secrets import secrets


REGION_ID = secrets['region_id']

# Init LCD
DEFAULT_I2C_ADDR = 0x27
i2c = I2C(1, sda=Pin(18), scl=Pin(19), freq=100000)
lcd = I2cLcd(i2c, DEFAULT_I2C_ADDR, 2, 16)

led_red_external = Pin(14, Pin.OUT)
led_green_external = Pin(15, Pin.OUT)

wlan = network.WLAN(network.STA_IF)


def connect_to_wifi():
    # Wi-Fi credentials
    SSID = secrets['ssid']
    PASSWORD = secrets['password']

    # Connect to network
    print("starting connection")    
    wlan.active(True)
    print("connecting...")
    wlan.connect(SSID, PASSWORD)

    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting for connection...')
        lcd.move_to(0, 0)
        lcd.putstr('Зачекайте...')
        sleep(1)

    if wlan.status() != 3:
        raise RuntimeError('network connection failed')
    else:
        print('connected')
        lcd.clear()
        lcd.putstr('Підключено')
        status = wlan.ifconfig()
        lcd.move_to(0, 1)
        lcd.putstr(status[0])
        led_green_external.on()


def main():
    connect_to_wifi()
    while True:
        try:
            response = urequests.get(
                f"https://siren.pp.ua/api/v3/alerts/{REGION_ID}",
                headers={"accept": "application/json"}
            )
            if response.status_code == 200:
                region_alerts = json.loads(response.text)
                print(region_alerts)
                if len(region_alerts[0]['activeAlerts']) > 0:
                    lcd.clear()
                    lcd.putstr("УВАГА!\nПовітр. тривога!")
                    led_green_external.off()
                    led_red_external.on()
                else:
                    lcd.clear()
                    lcd.putstr("Без тривоги")
                    lcd.move_to(0, 1)
                    lcd.putstr(region_alerts[0]['regionName'][:13] + "...")
                    led_green_external.on()
                    led_red_external.off()
            else:
                lcd.putstr("Помилка підключення")
                led_green_external.off()
                led_red_external.off()
        except Exception as e:
            print(e)
            lcd.clear()
            lcd.putstr("Щось пішло не так")
            led_green_external.off()
            led_red_external.off()
        sleep(30)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        led_green_external.off()
        led_red_external.off()
        lcd.clear()
        lcd.putstr("Завершено роботу")
        wlan.disconnect()
