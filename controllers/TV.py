import os, time
import threading
import subprocess
from omxplayer import OMXPlayer
from blinker import signal

class TV(threading.Thread):
    def __init__(self):
        super(TV, self).__init__()
        print("Initializing TV")
        self.red_alert = False
        self.player = None
        self.reset()

        #Register Events
        signal('SYSTEM_stopping').connect(self.clean_up)
        signal('tv.redalert').connect(self.alert)
        signal('alert.red.toggle').connect(self.alert)
        signal('code_47').connect(self.reset)

    def reset(self, sender='anonymous'):
        os.system('pkill omxplayer')
        self.player = OMXPlayer("http://repo.posttwo.pt/redalert.mp4", args=['--no-osd', '--no-keys', '-b', '--loop'])
        self.player.pause()

    def tv_set_pi(self):
        subprocess.call("echo 'as' | cec-client -s &", shell=True)
        #os.system('echo "as" | cec-client -s')

    def tv_set_chrome(self):
        subprocess.call("echo 'txn 4f:82:20:00' | cec-client -s &", shell=True)
        #os.system('echo "txn 4f:82:20:00" | cec-client -s')

    def alert(self, sender='anonymous'):
        if not self.red_alert:
            self.red_alert = True
            self.tv_set_pi()
            print("RED ALERT ON")
            self.player.set_position(0)
            self.player.play()
        else:
            self.red_alert = False
            self.tv_set_chrome()
            self.player.pause()

    def clean_up(self, sender='anonymous'):
        print("TV Cleaning Up")
        self.player.quit()