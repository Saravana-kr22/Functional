from .nordic import NordicDut
from threading import Thread

def create_dut_object(test_config):
    dut_object =  NordicDut(test_config)
    thread = Thread(target=dut_object._start_logging)
    thread.start()
    dut_object.factory_reset_dut()
    return dut_object