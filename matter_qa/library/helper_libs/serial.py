import logging
import sys
from serial import Serial


log = logging.getLogger("serial")

class SerialConnection:
    def __init__(self, serial_config):
        self.port = serial_config.serial_port
        self.baudrate = serial_config.baudrate
        self.timeout = serial_config.timeout

        try:
            self.serial_object = Serial(self.port, self.baudrate, timeout=self.timeout)
        except Exception as e:
            log.error(f"could not connect to Nordic DUT: {e}")
            sys.exit(1)

    def send_command(self, command):
        try:
            self.serial_object.write(command)
            self.serial_object.flush()
        except Exception as e:
            self.log.error(str(e), exc_info=True)

    def open_serial_connection(self):
        try:
            if not self.serial_port_obj.is_open:
                logging.info("Opening Serial Port")
                self.serial_object.open()
        except Exception as e:
            log.error(e,exc_info=True)

    def close_serial_connection(self):
        self.serial_object.close()