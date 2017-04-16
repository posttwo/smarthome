from blinker import signal
from lifxlan import *
import threading, queue

class Lights(threading.Thread):

    def __init__(self):
        super(Lights, self).__init__()
        print("Initializing Lights")

        #TODO ability to add more lights
        self.lifx  = LifxLAN(1)
        self.light = self.lifx.get_lights()[0]
        self.name  = self.light.get_mac_addr()
        self.old_color = None
        self.red_alert = False
        self.cinema = False
        print("Light " + self.name + " added")

        #Register events
        signal('SYSTEM_stopping').connect(self.clean_up)
        signal('lights.on').connect(self.turn_on)
        signal('lights.off').connect(self.turn_off)
        signal('lights.toggle').connect(self.toggle_power)
        signal('lights.cinema.toggle').connect(self.toggle_cinema)
        signal('lights.cinema.on').connect(self.set_cinema)
        signal('lights.cinema.off').connect(self.unset_cinema)
        signal('lights.brightness').connect(self.toggle_brightness)
        signal('alert.red.toggle').connect(self.toggle_red_alert)
        signal('lights.redalert.on').connect(self.set_red_alert)
        signal('lights.redalert.off').connect(self.unset_red_alert)
        signal('code_47').connect(self.normalize)

    def normalize(self, sender='anonymous'):
        self.shout("normalizing")
        self.old_color = None
        self.cinema = False
        self.light.set_color([0, 0, 65535, 2500], 500, True)

    def toggle_power(self, sender='anonymous'):
        if self.get_power():
            self.turn_off()
        else:
            self.turn_on()

    def toggle_cinema(self, sender='anonymous'):
        if self.cinema:
            self.unset_cinema()
        else:
            self.set_cinema()

    def set_cinema(self, sender='anonymous'):
        self.cinema = True
        self.shout("setting cinema")
        self.old_color = self.light.get_color()
        self.light.set_color((65535,65535,13107,2500), 500, True)
        self.turn_on()

    def unset_cinema(self, sender='anonymous'):
        self.cinema = False
        self.shout("disabling cinema")
        self.light.set_color(self.old_color, 500, True)

    def toggle_brightness(self, sender='anonymous'):
        self.shout("changing brightness")
        color = list(self.get_state())
        bright = color[2]
        if bright < 65535:
            color[2] = color[2] + 13107
            self.light.set_color(color, 500, True)
        else:
            color[2] = 13107
            self.light.set_color(color, 500, True)

    def toggle_red_alert(self, sender='anonymous'):
        if self.red_alert:
            self.unset_red_alert()
        else:
            self.set_red_alert()

    def set_red_alert(self, sender='anonymous'):
        self.shout("setting red alert status")
        self.red_alert = True
        t1 = threading.Thread(target=self.alert)
        t1.start()

    def unset_red_alert(self, sender='anonymous'):
        self.shout('unsetting red alert status')
        self.red_alert = False

    def alert(self):
        self.lifx.set_power_all_lights("on")
        while self.red_alert:
            self.lifx.set_color_all_lights([0, 65535, 65535, 2500], 500, True)
            sleep(0.8)
            self.lifx.set_color_all_lights([0, 0, 65535, 2500], 500, True)
            sleep(0.8)

    def turn_on(self, sender='anonymous'):
        self.shout("turning on")
        self.lifx.set_power_all_lights('on')

    def turn_off(self, sender='anonymous'):
        self.shout("turning_off")
        self.lifx.set_power_all_lights('off')

    def get_state(self):
        return self.light.get_color()

    def get_power(self):
        power = self.light.get_power()
        if power == 0:
            return False
        return True

    #Clean Up Aisle

    def shout(self, message):
        print("Light " + self.name + " | " + message)

    def join(self, timeout=None):
        self.clean_up()
        super(Lights, self).join(timeout)

    def clean_up(*args, **kwargs):
        print("Lights Cleaning Up")