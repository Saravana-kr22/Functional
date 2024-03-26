#
#
#  Copyright (c) 2023 Project CHIP Authors
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
import datetime
import importlib.util
import traceback
import time
import logging
import os
from threading import Event, Thread
import sys
from matter_qa.library.base_test_classes.dut_base_class import BaseDutNodeClass
from matter_qa.library.helper_libs.serial import SerialConnection

global log 
log = logging.getLogger("nordic")
event_closer = Event()


class SerialConfig:
    def __init__(self,serial_port, baudrate, timeout) -> None:
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.timeout = timeout

class NordicDut(BaseDutNodeClass):
    def __init__(self, test_config) -> None:
        super().__init__()
        self.dut_config = test_config.dut_config.nordic
        serial_config = SerialConfig(test_config.dut_config.nordic.serial_port,
                                     test_config.dut_config.nordic.serial_baudrate,
                                     test_config.dut_config.nordic.serial_timeout)
        self.serial_session = SerialConnection(serial_config)
        self.command = self.dut_config.command
        self.test_config = test_config

        try:
            self.serial_session.open_serial_connection()
        except Exception as e:
            log.error("Could not establish Serial connection {}".format(e))
            sys.exit(1)


    def reboot_dut(self):
        pass

    def start_matter_app(self):
        pass

    def factory_reset_dut(self):
        try:
            log.info("Starting to Reset Nordic as the DUT")
            for i in range(1, 3):
                if self.serial_session.serial_object.is_open:
                    self.serial_session.send_command(self.command.encode('utf-8'))
                    time.sleep(5)
                else:
                    self.serial_session.open_serial_connection()
                    self.serial_session.send_command(self.command.encode('utf-8'))
        except Exception as e:
            log.error(e, exc_info=True)
        return True
    
    def start_logging(self, file_name):
        pass

    def _start_logging(self, file_name=None) -> bool:
        global event_closer
        if not self.serial_session.serial_object.is_open:
            self.serial_session.open_serial_connection()
        if self.serial_session.serial_object.is_open:
            while self.serial_session.serial_object.is_open:
                if file_name is not None:
                    log_file = file_name
                else:
                    try:
                        log_file = os.path.join(self.test_config.iter_log_path, "Dut_log_{}_"
                                            .format(str(self.test_config.current_iteration)) +
                                            str(datetime.datetime.now().isoformat()).replace(':', "_").replace('.', "_")
                                            + ".log"
                                            )
                        
                        logging.info("started to read buffer")
                        dut_log = self.serial_session.serial_object.read_until(b'Test-iteration completed').decode()
                        logging.info("completed read from buffer")
                        if dut_log == '':
                            log.info("data not present in buffer breaking from read loop")
                            break
                        with open(log_file, 'w') as fp:
                            fp.write(f" \n\n  Dut log of {self.test_config.current_iteration} iteration \n")
                            fp.write(dut_log)
                            logging.info("completed write to file")
                    except Exception as e:
                        log.info(f"Waiting for current_iteration to be assigned, {e}")
            self.serial_session.close_serial_connection()
        else:
            log.info("Failed to read the log in thread")
            sys.exit()
        return True

    def stop_logging(self):
        global event_closer
        event_closer.set()
        return True
    
    def pre_testcase_loop(self):
        pass
    
    def pre_iteration_loop(self):
        pass

    def post_iteration_loop(self):
        try:
            if self.serial_session.serial_object.is_open:
                self.serial_session.send_command(b"Test-iteration completed")
                time.sleep(5)
        except Exception as e:
            log.error("Could not establish Serial connection {}".format(e))
