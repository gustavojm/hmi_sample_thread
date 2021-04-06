import os, sys, time
import json
import queue as Queue
import gi
from curses.ascii import NUL
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk, Gdk, GObject
import os
import time

from socketclientthread import SocketClientThread, ClientCommand, ClientReply

SERVER_ADDR = '192.168.1.12', 1234


class SampleGUIClientWindow():

    def __init__(self, parent=None):
        self.create_client()

        self.builder = Gtk.Builder()
                
        self.builder.add_from_file("gui.glade")
        
        self.window = self.builder.get_object("sample_gui_threads")
        self.btn_switch = self.builder.get_object("btn_switch")
        self.logs_TextView = self.builder.get_object("logs_TextView")
        self.lbl_posActArm = self.builder.get_object("lbl_posActArm")
        self.logs_buffer = self.logs_TextView.get_buffer(); 

        señales = {
            "window_close":Gtk.main_quit,
            "on_cmd_btn1_button_press_event": self.doit,
            "on_btn_switch_button_press_event": self.on_btn_switch_button_press_event,
            "on_btn_switch_state_set": self.on_btn_switch_state_set
        }
        self.builder.connect_signals(señales)

        self.client.cmd_q.put(ClientCommand(ClientCommand.CONNECT, SERVER_ADDR))        
        self.create_timers()
        self.window.show()

    def create_client(self):
        self.client = SocketClientThread()
        self.client.start()

    def create_timers(self):
        GObject.threads_init()
        self.client_reply_timer = GObject.timeout_add(10, self.on_client_reply_timer)
        self.telemetry_timer = GObject.timeout_add(100, self.telemetria)

    def on_btn_switch_state_set(self, widget, state):
        return True
        
    def on_btn_switch_button_press_event(self, widget, event):
        # self.client.cmd_q.put(ClientCommand(ClientCommand.CONNECT, SERVER_ADDR))
        
        commands_obj = {
          "commands": [
            {"command": "CONTROL_ENABLE"
            },
          ]
        }
        
        self.client.cmd_q.put(ClientCommand(ClientCommand.SEND, json.dumps(commands_obj)))
        self.client.cmd_q.put(ClientCommand(ClientCommand.RECEIVE))
        # self.client.cmd_q.put(ClientCommand(ClientCommand.CLOSE))
        
    def doit(self, widget, event):
        self.telemetria()

    def telemetria(self):
        # self.client.cmd_q.put(ClientCommand(ClientCommand.CONNECT, SERVER_ADDR))        
        commands_obj = {
          "commands": [
            {"command": "CONTROL_ENABLE"
            },
            {"command": "LOGS", "pars": {
                        "quantity": 10
                        }    
            },
            {"command": "TELEMETRIA"
            },
            {"command": "PROTOCOL_VERSION"
            }
          ]
        }
        
        self.client.cmd_q.put(ClientCommand(ClientCommand.SEND, json.dumps(commands_obj)))
        self.client.cmd_q.put(ClientCommand(ClientCommand.RECEIVE))
        # self.client.cmd_q.put(ClientCommand(ClientCommand.CLOSE))
        return True  # to allow repetition of the timeout

    def on_client_reply_timer(self):
        try:
            reply = self.client.reply_q.get(block=False)
            status = "SUCCESS" if reply.type == ClientReply.SUCCESS else "ERROR"
            if reply.data is not None:
                self.log('%s' % (reply.data))
                self.update_ui(reply.data)
                
        except Queue.Empty:
            pass
        return True

    def log(self, msg):
        timestamp = '[%010.3f]' % time.clock()
        # end_iter = self.logs_buffer.get_end_iter()
        # self.logs_buffer.insert(end_iter, str(msg))
        
    def update_ui(self, data): 
        try: 
            objeto_json = json.loads(str(data).rstrip('\0'))                    
    
            try: 
                self.btn_switch.set_state(objeto_json["CONTROL_ENABLE"]["ACK"])
                self.btn_switch.set_active(self.btn_switch.get_state())
    
                for log in objeto_json["LOGS"]["DEBUG_MSGS"]:
                    print(log)
    
                self.lbl_posActArm.set_text(str(objeto_json["TELEMETRIA"]["ARM"]["posAct"]))
                print("Stalled ARM: %s" % objeto_json["TELEMETRIA"]["ARM"]["stalled"])                    
                print("Posición actual POLE: %i" % objeto_json["TELEMETRIA"]["POLE"]["posAct"])
                print("Protocol Version: %s" % objeto_json["PROTOCOL_VERSION"]["Version"])
            except KeyError:
                print("no encontrado")
        except ValueError as e:
            print("Error decodificando JSON")


#-------------------------------------------------------------------------------
if __name__ == "__main__":
    mainwindow = SampleGUIClientWindow()
    Gtk.main()
    
