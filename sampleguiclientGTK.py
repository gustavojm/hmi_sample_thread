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

SERVER_ADDR = '192.168.2.24', 1234


class SampleGUIClientWindow():

    def __init__(self, parent=None):
        self.create_client()

        self.builder = Gtk.Builder()
                
        self.builder.add_from_file("gui.glade")
        
        self.window = self.builder.get_object("sample_gui_threads")
        self.btn_switch = self.builder.get_object("btn_switch")
        self.logs_TextView = self.builder.get_object("logs_TextView")
        self.lbl_posActArm = self.builder.get_object("lbl_posActArm")
        self.used_mem_bar = self.builder.get_object("used_mem_bar")
        self.min_mem_bar = self.builder.get_object("min_mem_bar")
        self.logs_buffer = self.logs_TextView.get_buffer(); 
        self.temp1_bar = self.builder.get_object("temp1_bar")
        self.temp2_bar = self.builder.get_object("temp2_bar")

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
        #self.client.cmd_q.put(ClientCommand(ClientCommand.CONNECT, SERVER_ADDR))        
        commands_obj = {
          "commands": [
            {"command": "CONTROL_ENABLE"
            },
          ]
        }
        
        self.client.cmd_q.put(ClientCommand(ClientCommand.SEND, json.dumps(commands_obj)))
        self.client.cmd_q.put(ClientCommand(ClientCommand.RECEIVE))
        #self.client.cmd_q.put(ClientCommand(ClientCommand.CLOSE))
        
    def doit(self, widget, event):
        self.telemetria()

    def telemetria(self):
        # self.client.cmd_q.put(ClientCommand(ClientCommand.CONNECT, SERVER_ADDR))        
        commands_obj = {
            "commands": [
                #{"command": "CONTROL_ENABLE"
                #},
                {"command": "LIFT_UP",
                 "pars": {
                    "dir" : "up"
                 }
                },
                {"command": "LOGS", "pars": {
                            "quantity": 10
                            }    
                },
                {"command": "TELEMETRIA"
                },
                {"command": "PROTOCOL_VERSION"
                },
                {"command": "ARM_FREE_RUN",
                          "pars": {
                            "dir": "CW",
                            "speed": 8 
                            }                     
                },
                {"command": "POLE_CLOSED_LOOP",
                 "pars": {
                    "posCmd": 60755
                    }                     
                },
                {"command": "MEM_INFO",
                },
                {"command": "TEMPERATURE_INFO",
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
            
            if status == "ERROR" :
                self.client.cmd_q.put(ClientCommand(ClientCommand.CONNECT, SERVER_ADDR))
                
            if reply.data is not None:
                self.update_ui(reply.data)
            
        except Queue.Empty:
            pass
        return True

    def log(self, msg):
        timestamp = '[%010.3f]' % time.clock()
        end_iter = self.logs_buffer.get_end_iter()
        self.logs_buffer.insert(end_iter, str(msg))
        
    def update_ui(self, data): 
        try: 
            objeto_json = json.loads(str(data).rstrip('\0'))                    
            print(str(data))
            try: 
                if "CONTROL_ENABLE" in objeto_json: 
                    self.btn_switch.set_state(objeto_json["CONTROL_ENABLE"]["ACK"])                
                    self.btn_switch.set_active(self.btn_switch.get_state())
    
                for log in objeto_json["LOGS"]["DEBUG_MSGS"]:
                    self.log('%s' % (log))
                    #print(log)
    
                self.temp1_bar.set_fraction(objeto_json["TEMPERATURE_INFO"]["TEMP1"] / 100)
                self.temp1_bar.set_text(str(format(round(objeto_json["TEMPERATURE_INFO"]["TEMP1"], 2), '.2f')))
                self.temp2_bar.set_fraction(objeto_json["TEMPERATURE_INFO"]["TEMP2"] / 100)
                self.temp2_bar.set_text(str(format(round(objeto_json["TEMPERATURE_INFO"]["TEMP2"], 2), '.2f')))
                print("Stalled ARM: %s" % objeto_json["TELEMETRIA"]["ARM"]["stalled"])
                print("Protocol Version: %s" % objeto_json["PROTOCOL_VERSION"]["Version"])
                self.used_mem_bar.set_fraction(((objeto_json["MEM_INFO"]["MEM_FREE"]) / (objeto_json["MEM_INFO"]["MEM_TOTAL"])))
                self.used_mem_bar.set_text("Free: " + str(objeto_json["MEM_INFO"]["MEM_FREE"]))
                self.min_mem_bar.set_fraction(((objeto_json["MEM_INFO"]["MEM_MIN_FREE"]) / (objeto_json["MEM_INFO"]["MEM_TOTAL"])))
                self.min_mem_bar.set_text("Min: " + str(objeto_json["MEM_INFO"]["MEM_MIN_FREE"]))
            except KeyError:
                print("no encontrado")
        except ValueError as e:
            print("Error decodificando JSON")
            print(str(data));


#-------------------------------------------------------------------------------
if __name__ == "__main__":
    mainwindow = SampleGUIClientWindow()
    Gtk.main()
    
