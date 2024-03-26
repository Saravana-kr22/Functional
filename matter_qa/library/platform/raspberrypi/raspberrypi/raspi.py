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
import logging
import os.path
import threading
import time
import traceback
import sys

from matter_qa.library.base_test_classes.dut_base_class import BaseDutNodeClass
from matter_qa.library.helper_libs.ssh import SSH

global log 
log = logging.getLogger("raspi")

class SSHConfig:
    def __init__(self, hostname, username, password):
        self.hostname = hostname
        self.username = username
        self.password = password

class Raspi(BaseDutNodeClass):
    def __init__(self, test_config) -> None:
        super().__init__()

        self.dut_config = test_config.dut_config.rpi
        ssh_config = SSHConfig(test_config.dut_config.rpi.rpi_hostname,
                               test_config.dut_config.rpi.rpi_username,
                               test_config.dut_config.rpi.rpi_password
                            )
  
        self.ssh_session = SSH(ssh_config)
        self.matter_app = self.dut_config.app_config.matter_app
        self.test_config = test_config

        try:
            self.ssh_session.open_ssh_connection()
        except Exception as e:
            log.error("Could not establish SSH connection {}".format(e))
            sys.exit(1)
        
    def reboot_dut(self):
        try:
            reboot_command = f"sudo reboot"
            self.ssh_session.send_command_no_output(reboot_command)
            return True
        except Exception as e:
            log.error(e, exc_info=True)
            return True

    def factory_reset_dut(self):
        try:
            log.info("Starting to Reset RPI as the DUT")
            # Executing the  'ps aux | grep process_name' command to find the PID value to kill
            self._kill_app()
            time.sleep(5)
            log.info("Example App has been killed")
            self._delete_storage()
            self.ssh_session.close_ssh_connection()

        except Exception as e:
            log.error(e, exc_info=True)
            
    
    def _kill_app(self):
        command = f'ps aux | grep "{self.matter_app}"'
        pid_val = self.ssh_session.send_command_receive_output(command,hide=True)
        pid_output = pid_val.stdout
        pid_lines = pid_output.split('\n')
        for line in pid_lines:
            try:
                if self.matter_app in line:
                    pid = line.split()[1]
                    if "grep" not in line:
                        log.info("Displaying the pid and process to terminate {}".format(line))
                        kill_command = f"kill {pid}"
                        self.ssh_session.send_command_no_output(kill_command)
            except Exception as e:
                log.error(e)
                traceback.print_exc()
                return True
            
    def _delete_storage(self):
        self.ssh_session.send_command_no_output('rm -rf /tmp/chip_*')

    def start_matter_app(self):
        self._start_matter_app()

    def _start_matter_app(self):
        try:
            self.ssh_session.open_ssh_connection()
            raspi_log_file = self.ssh_session.send_command_receive_output(self.matter_app, warn=True, hide=True, pty=False)
            self._start_logging(raspi_log_file)
        except Exception as e:
            log.error(e, exc_info=True)
            traceback.print_exc()
        return True

    def start_logging(self, file_name):
        pass

    def _start_logging(self, raspi_log, file_name=None):

        try:
            if file_name is not None:
                log_file = file_name
            else:
                log_file = os.path.join(self.test_config.iter_log_path, "Dut_log_{}_"
                                    .format(str(self.test_config.current_iteration)) +
                                    str(datetime.datetime.now().isoformat()).replace(':', "_").replace('.', "_")
                                    + ".log"
                                    )
            with open(log_file, 'a') as fp:
                fp.write(f" \n\n  Dut log of {self.test_config.current_iteration} iteration \n")
                fp.write(raspi_log.stdout)
            return True
        except Exception as e:
            log.error(e, exc_info=True)

    def pre_testcase_loop(self):
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._start_matter_app)
        self.thread.start()
        time.sleep(2)

    def stop_logging(self):
        # As we are killing the example while factory reset this will stop the logging process
        pass
    
    def pre_iteration_loop(self):
        pass
    
    def post_iteration_loop(self):
        pass
