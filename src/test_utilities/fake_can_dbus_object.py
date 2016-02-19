import dbus
import dbus.service
import dbus.mainloop.glib
import time
import json
import can_dbc_reader
import threading
import random
import signal

signal.signal(signal.SIGINT, signal.SIG_DFL)

from gi.repository import Gtk as gtk

class can_medium_speed(dbus.service.Object):

    def __init__(self, conn, object_path='/bus/can/can_medium_speed/object'):
        dbus.service.Object.__init__(self, conn, object_path)
        self.name_of_bus = dbus.service.BusName('bus.can.medium_speed', bus=dbus.SessionBus())
        self.can_table = can_dbc_reader.get_can('fake_utf8_can_dbc.dbc')
        self.state_table = {}
        self.signal_table = {}
        for key in self.can_table:
            self.state_table[key] = None 

        for arb_id, params in self.can_table.items():
            for signal, values in params['species'].items():
                self.signal_table[signal] = self.can_table[arb_id]['species'][signal]['value']

    # # Magic code to create a bitmask of length
    # # maximum length is actuall the maximum number of bits we can have in each frame, we default to an 8 byte frame
    # def get_mask_ones(self, length, maximum=0xFFFFFFFFFFFFFFFF):
    #     b = maximum << length
    #     c = b & maximum
    #     return (c^maximum)

    # def map_values(self, arb_id, payload):
    #     num_bits = self.can_table[arb_id]['frame_bytes'] * 8
    #     for signal, specs in self.can_table[arb_id]['species'].items():
    #         sig_value = ((payload >> (num_bits - (specs['end_bit']-specs['length']+1) ) & (self.get_mask_ones(length=specs['length'], maximum = ((2**num_bits)-1)))) * specs['factor']) + specs['offset']
    #         if specs['value'] == sig_value:
    #             pass
    #         else:
    #             specs['value'] = sig_value
    #             self.signal_table[signal] = sig_value
    #             self.update_frame(json.dumps({'signal_type':'VEHICLE_SIGNAL', 'signal_id':signal, 'value':sig_value}))
    #             # if arb_id == 800:
    #             #     print(payload)
    #             #     print(signal, specs)

    @dbus.service.signal('bus.can.update.can_medium_speed')
    def update_frame(self, msg=None):
        pass

    @dbus.service.method('bus.can.request.can_medium_table')
    def request_can_table(self):
        print("INVOKED METHOD")
        subscribed_table = self.signal_table
        return json.dumps(subscribed_table)


def emit_can_signals(can_obj):
    value = 0
    while True:
        for signal in can_obj.signal_table:
            random_value = random.randint(0,15)
            can_obj.signal_table[signal] = random_value
            can_obj.update_frame(json.dumps({'signal_type':'VEHICLE_SIGNAL', 'signal_id':signal, 'value':random_value}))
        value += 1
        time.sleep(5)

    # can_interface = 'can0'
    # bus = can.interface.Bus(can_interface, bustype='socketcan_native')

    # for message in bus:
    #     if int(message.arbitration_id) not in can_object.can_table:
    #         print('!!! WARNING UNKNOWN CAN FRAME !!!')

    #     elif int(message.arbitration_id) not in can_object.can_table:
    #         can_object.state_table[int(message.arbitration_id)] = message.data
    #         can_object.map_values(arb_id = int(message.arbitration_id), payload = int.from_bytes(message.data, byteorder='big', signed=False))
    #         continue

    #     elif message.data == can_object.state_table[int(message.arbitration_id)]: 
    #         continue

    #     else:
    #         can_object.state_table[int(message.arbitration_id)] = message.data
    #         can_object.map_values(arb_id = int(message.arbitration_id), payload = int.from_bytes(message.data, byteorder='big', signed=False))



if __name__ == '__main__':

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    can_object = can_medium_speed(dbus.SessionBus())

    signal_thread = threading.Thread(target=emit_can_signals, args=(can_object,))
    signal_thread.start()

    print('Starting GTK Main')
    gtk.main()
    # can_interface = 'can0'
    # bus = can.interface.Bus(can_interface, bustype='socketcan_native')

    # for message in bus:
    #     if int(message.arbitration_id) not in can_object.can_table:
    #         print('!!! WARNING UNKNOWN CAN FRAME !!!')

    #     elif int(message.arbitration_id) not in can_object.can_table:
    #         can_object.state_table[int(message.arbitration_id)] = message.data
    #         can_object.map_values(arb_id = int(message.arbitration_id), payload = int.from_bytes(message.data, byteorder='big', signed=False))
    #         continue

    #     elif message.data == can_object.state_table[int(message.arbitration_id)]: 
    #         continue

    #     else:
    #         can_object.state_table[int(message.arbitration_id)] = message.data
    #         can_object.map_values(arb_id = int(message.arbitration_id), payload = int.from_bytes(message.data, byteorder='big', signed=False))

