import threading
import time
from colorama import init, Back, Style
from flask import Flask, request
from blinker import signal
from controllers import Lights
from controllers import TV
from pad4pi import rpi_gpio
from flask.ext.jsonpify import jsonify

class Run:
    def __init__(self):
        self.input_buffer = ""

    def main(self):
        try:
            init()

            print(Back.WHITE + 'Initializing SmartTwo Controller.' + Style.RESET_ALL)
            #WebAPI
            threading._start_new_thread(flaskThread, ())

            #Devices
            ##Lights
            lights = Lights.Lights()
            lights.start()

            ##TV
            tv = TV.TV()
            tv.start()

            print(Back.WHITE + 'Initializing Keypad.' + Style.RESET_ALL)
            ##Keypad
            KEYPAD = [
                [1, 2, 3, "A"],
                [4, 5, 6, "B"],
                [7, 8, 9, "C"],
                ["*", 0, "#", "D"]
            ]
            factory = rpi_gpio.KeypadFactory()
            ROW_PINS = [2, 3, 4, 17]  # BCM numbering
            COL_PINS = [22, 27, 10, 9]  # BCM numbering
            self.keypad = factory.create_keypad(keypad=KEYPAD, row_pins=ROW_PINS, col_pins=COL_PINS)
            self.keypad.registerKeyPressHandler(self.key_pressed)

            print(Back.GREEN + 'SmartTwo Controller Started' + Style.RESET_ALL)
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            print(Back.RED + "Stopping SmartTwo Controller" + Style.RESET_ALL)
            signal('SYSTEM_stopping').send(self)
        finally:
            self.keypad.cleanup()

    def broadcast(self, path):
        signal(path).send(self)

    def key_pressed(self, key):
        print("Pressed {} key".format(key))
        try:
            int_key = int(key)
            if int_key >= 0 and int_key <= 9:
                self.digit_entered(key)
        except ValueError:
            self.non_digit_entered(key)

    def digit_entered(self, key):
        self.input_buffer += str(key)

    def non_digit_entered(self, key):
        if key == '#':
            print("Code: " + self.input_buffer)
            signal('code_' + self.input_buffer).send(self)
            self.input_buffer = ""
        if key == '*':
            print('Clearing Input Buffer')
            self.input_buffer = ""
        if key == 'A':
            signal('lights.toggle').send(self)
        if key == 'B':
            signal('lights.brightness').send(self)
        if key == 'C':
            signal('lights.cinema.toggle').send(self)
        if key == 'D':
            signal('alert.red.toggle').send(self)


app = Flask(__name__)
run = Run()

def flaskThread():
    print('Starting WebAPI')
    app.run(host="0.0.0.0", port="9000")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def webRequest(path):
    run.broadcast(path)
    return jsonify(message="Cool")

run.main()