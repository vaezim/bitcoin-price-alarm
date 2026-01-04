import flask
from gtts import gTTS
import os, requests, time, threading


class CryptoPriceAlarm:
    def __init__(self):
        self.API = "https://api.coinbase.com/v2/prices/BTC-USD/spot"

        self.PRICE_CHECK_INTERVAL = 15  # every T seconds

        self.last_time_sound_played = 0
        self.MIN_TIME_BETWEEN_SOUND_PLAYS = 10 * 60  # seconds

        self.above_limits = []
        self.below_limits = []

    def run(self):
        price = self.get_current_price()
        if price == None:
            self.play_sound(f"Failed to get current price. Exitting.")
            return
        self.play_sound(f"Bitcoin price alarm is running. Current price is {price} USD")
        while True:
            time.sleep(self.PRICE_CHECK_INTERVAL)
            price = self.get_current_price()
            if price == None:
                self.play_sound(f"Failed to get current price. Exiting.")
                return
            self.try_alarm(price)

    def get_current_price(self):  # USD
        try:
            response = requests.get(self.API)
            if response.status_code != 200:
                raise f"[-] Response status code = {response.status_code}"
        except:
            raise f"[-] Failed to send GET request to API {self.API}"
        content = response.json()
        try:
            price = int(round(float(content["data"]["amount"])))
        except:
            raise f"[-] Failed to extract price from json:\n{content}"
        return price

    def try_alarm(self, price):
        if (
            time.time() - self.last_time_sound_played
            < self.MIN_TIME_BETWEEN_SOUND_PLAYS
        ):
            return
        sound_played = False
        for limit in self.above_limits:
            if price > limit:
                self.play_sound(
                    f"UP! Price jumped above {limit} limit. Current price is {price}."
                )
                sound_played = True
        for limit in self.below_limits:
            if price < limit:
                self.play_sound(
                    f"DOWN! Price dropped below {limit} limit. Current price is {price}."
                )
                sound_played = True
        if sound_played:
            self.last_time_sound_played = time.time()

    def play_sound(self, text):
        tts = gTTS(text)
        tts.save("price.mp3")
        os.system("mpg123 -q price.mp3")  # sudo apt install mpg123


if __name__ == "__main__":

    # Price alarm (separate thread)
    alarm = CryptoPriceAlarm()
    t = threading.Thread(target=alarm.run, daemon=True)
    t.start()

    # Web server (main thread)
    app = flask.Flask(__name__)
    try:
        HTML_FILE = "index.html"
        with open(HTML_FILE, "r") as f:
            HTML = f.read()
    except:
        raise f"[-] Failed to read {HTML_FILE} file."

    @app.route("/", methods=["GET", "POST"])
    def index():
        if flask.request.method == "POST":

            # Remove the limit if its checkbox is checked
            remove_list = flask.request.form.getlist("remove_above")
            for _limit in remove_list:
                limit = int(_limit)
                if limit in alarm.above_limits:
                    alarm.above_limits.remove(limit)
            remove_list = flask.request.form.getlist("remove_below")
            for _limit in remove_list:
                limit = int(_limit)
                if limit in alarm.below_limits:
                    alarm.below_limits.remove(limit)

            # Add below and above limits to alarm
            above = flask.request.form["above"]
            above = int(above) if len(above) else None
            below = flask.request.form["below"]
            below = int(below) if len(below) else None
            if above:
                alarm.above_limits.append(above)
                alarm.above_limits.sort()
            if below:
                alarm.below_limits.append(below)
                alarm.below_limits.sort()
        return flask.render_template_string(HTML, alarm=alarm)

    app.run(host="0.0.0.0", port=8080, debug=True, use_reloader=False)
