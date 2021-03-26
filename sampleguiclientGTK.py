"""
Sample GUI using SocketClientThread for socket communication, while doing other
stuff in parallel.

Eli Bendersky (eliben@gmail.com)
This code is in the public domain
"""
import os, sys, time
import json
import queue as Queue
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk, Gdk, GObject
import os
import time


from socketclientthread import SocketClientThread, ClientCommand, ClientReply

SERVER_ADDR = '192.168.1.12', 1234

class SampleGUIClientWindow():
    def __init__(self, parent=None):
        self.create_client()
        self.create_timers()

        self.builder = Gtk.Builder()
                
        self.builder.add_from_file("gui.glade")
        
        self.window = self.builder.get_object("sample_gui_threads")
        self.logs_box = self.builder.get_object("logs_box")

        señales = {
            "window_close":Gtk.main_quit,
            "on_cmd_btn1_button_press_event": self.on_doit
        }
        self.builder.connect_signals(señales)
        
        self.window.show()

    def create_client(self):
        self.client = SocketClientThread()
        self.client.start()

    def create_timers(self):
        GObject.threads_init()
        self.client_reply_timer = GObject.timeout_add(10, self.on_client_reply_timer)

    def on_doit(self, widget, event):
        self.client.cmd_q.put(ClientCommand(ClientCommand.CONNECT, SERVER_ADDR))
        
        commands_obj = {
          "commands": [
            {"command": "LOGS", "pars": {
                        "quantity": 10 
                        }    
            },
            {"command": "TELEMETRIA"
            },
          ]
        }
        
        self.client.cmd_q.put(ClientCommand(ClientCommand.SEND, json.dumps(commands_obj)))
        self.client.cmd_q.put(ClientCommand(ClientCommand.RECEIVE))
        self.client.cmd_q.put(ClientCommand(ClientCommand.CLOSE))

    def on_client_reply_timer(self):
        try:
            reply = self.client.reply_q.get(block=False)
            status = "SUCCESS" if reply.type == ClientReply.SUCCESS else "ERROR"
            if reply.data is not None:
                self.log('%s' % (reply.data))
        except Queue.Empty:
            pass
        return True

    def log(self, msg):
        timestamp = '[%010.3f]' % time.clock()
        print(str(msg))
        objeto_json = json.loads(str(msg))
        
        for log in objeto_json["LOGS"]["DEBUG_MSGS"]:
            print(log)

        print("Posición actual ARM: %i" % objeto_json["TELEMETRIA"]["ARM"]["posAct"])
        print("Stalled ARM: %s" % objeto_json["TELEMETRIA"]["ARM"]["stalled"])
        
        
        print("Posición actual POLE: %i" % objeto_json["TELEMETRIA"]["POLE"]["posAct"])
                
        self.logs_box.set_text(timestamp + ' ' + str(msg))
        print(str(msg))

#-------------------------------------------------------------------------------
if __name__ == "__main__":
    mainwindow = SampleGUIClientWindow()
    Gtk.main()


