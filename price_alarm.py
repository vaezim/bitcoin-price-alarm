from gtts import gTTS
from statistics import mean
import os, json, requests, time


class CryptoPriceAlarm:
    def __init__(self):
        self.API = "https://api.coinbase.com/v2/prices/BTC-USD/spot"

        self.last_time_sound_played = 0
        self.MIN_TIME_BETWEEN_SOUND_PLAYS = 10 * 60  # seconds
        self.MIN_DIFF_TO_PLAY_SOUND = 1000  # USD

        self.WINDOW_TIME = 10 * 60  # seconds
        self.PRICE_CHECK_INTERVAL = 15  # seconds
        self.WINDOW_SIZE = self.WINDOW_TIME // self.PRICE_CHECK_INTERVAL
        self.window = []  # Holds the prices of the last 10 minutes.

    def run(self):
        price = self.get_current_price()
        if price == None:
            print("[-] Failed to get current price.")
            return
        self.play_sound(f"Bitcoin price alarm is running. Current price is {price} USD")
        self.window.append(price)
        while True:
            time.sleep(self.PRICE_CHECK_INTERVAL)
            price = self.get_current_price()
            if price == None:
                print("[-] Failed to get current price.")
                break
            self.try_alarm(price)
            self.window.append(price)
            while len(self.window) > self.WINDOW_SIZE:
                self.window.pop(0)

    def get_current_price(self):  # USD
        try:
            response = requests.get(self.API)
            if response.status_code != 200:
                print(f"[-] Response status code = {response.status_code}")
                return None
        except:
            print(f"[-] Failed to send GET request to API {self.API}")
            return None
        content = json.loads(response.content.decode())
        try:
            price = float(content["data"]["amount"])
        except:
            print("[-] Failed to extract price from json.")
            return None
        return int(round(price))

    def try_alarm(self, price):
        avg = int(round(mean(self.window)))
        diff = price - avg
        if (
            abs(diff) < self.MIN_DIFF_TO_PLAY_SOUND
            or time.time() - self.last_time_sound_played
            < self.MIN_TIME_BETWEEN_SOUND_PLAYS
        ):
            return
        self.last_time_sound_played = time.time()
        if diff > 0:
            self.play_sound(f"UP, UP from {avg} to {price}")
        elif diff < 0:
            self.play_sound(f"DOWN, DOWN from {avg} to {price}")

    def play_sound(self, text):
        tts = gTTS(text)
        tts.save("price.mp3")
        os.system("mpg123 -q price.mp3")  # sudo apt install mpg123


if __name__ == "__main__":
    alarm = CryptoPriceAlarm()
    alarm.run()
