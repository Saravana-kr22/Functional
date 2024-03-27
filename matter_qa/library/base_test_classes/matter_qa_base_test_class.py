import logging
import datetime
import os
import traceback
import time
import importlib
import sys
import datetime
import inspect
import json

from matter_qa.library.helper_libs.logger import qa_logger
from matter_qa.library.helper_libs.exceptions import *
from matter_qa.library.helper_libs.utils import default_config_reader
from matter_qa.library.platform.dut_class import dut_class
from matter_qa.library.helper_libs.matter_testing_support import MatterBaseTest
from matter_qa.configs.config import TestConfig
from matter_qa.library.base_test_classes.test_results_record import TestresultsRecord,TestResultEnums,IterationTestResultsEnums,SummaryTestResultsEnums,DUTInformationRecordEnums

from .test_result_observable import TestResultObservable
from .test_result_observer import TestResultObserver

from mobly.config_parser import ENV_MOBLY_LOGPATH, TestRunConfig

import chip
from chip.exceptions import ChipStackError
from chip import ChipDeviceCtrl
import chip.clusters as Clusters
import asyncio

log = logging.getLogger("base_tc")
class MatterQABaseTestCaseClass(MatterBaseTest):
    def __init__(self,*args) -> None:
        self.iteration_log_created = False
        self.analytics_dict ={}
        super().__init__(*args)
        self._start_test()
        self.fetch_dut_info_once_status = True
        
    def _start_test(self,**kwargs):
        
        self.test_config = self._config_reader(config=kwargs.get("test_config"))
        self.run_set_folder = self._create_run_set_folder()
        # need this logger to create log file for every iteration
        self.qa_logger = qa_logger()
        # create a dut object to use in TC
        self.dut = self._get_dut_obj()
        self.test_result_observable = TestResultObservable()
        #TODO fix this file business properly
        summary_file = os.path.join(self.run_set_folder, 'summary.json')
        self.test_result_observer = TestResultObserver(summary_file)
        self.test_result_observable.subscribe(self.test_result_observer)
        self.iteration_test_result = TestResultEnums.TEST_RESULT_FAIL
        self.current_iteration = 1
        self.total_number_of_iterations_passed = 0
        self.total_number_of_iterations_failed = 0
        self.total_number_of_iterations_error = 0
        self.list_of_iterations_failed = []

        summary_record = {SummaryTestResultsEnums.RECORD_TEST_NAME: self.tc_name,
                          SummaryTestResultsEnums.RECORD_TEST_CASE_ID: self.tc_id,
                          SummaryTestResultsEnums.RECORD_TEST_CLASS: type(self).__name__,
                          SummaryTestResultsEnums.RECORD_TEST_BEGIN_TIME: datetime.datetime.now().strftime(
                              "%d/%m/%Y %H:%M:%S"),
                          SummaryTestResultsEnums.RECORD_TOTAL_NUMBER_OF_ITERATIONS: self.test_config.general_configs.number_of_iterations,
                          SummaryTestResultsEnums.RECORD_TEST_STATUS: SummaryTestResultsEnums.RECORD_TEST_IN_PROGRESS,
                          SummaryTestResultsEnums.RECORD_PLATFORM: self.test_config.general_configs.platform_execution,
                          SummaryTestResultsEnums.RECORD_COMMISSIONING_METHOD: self.matter_test_config.commissioning_method,
                          SummaryTestResultsEnums.RECORD_ANALYTICS_METADATA:
                              list(self.test_config.__dict__["general_configs"].__dict__[
                                  "analytics_parameters"].__dict__.keys())
                          }
    
        self.test_results_record = TestresultsRecord(summary_record)
        self.test_result_observable.notify(self.test_results_record)

    def _config_reader(self, config=None):
       
        test_config = TestConfig(self.matter_test_config.reliability_tests_config)
        # to over write any default config parameters
        test_config = self._overwrite_test_config(test_config)
        return test_config

    def _overwrite_test_config(self,test_config):
        """
        overwrite the test config with test case specific parameters
        """
        if hasattr(test_config, 'test_case_config') and hasattr(getattr(test_config,'test_case_config'), type(self).__name__) :
          test_config.general_configs.number_of_iterations = getattr(test_config.test_case_config, type(self).__name__).number_of_iterations
        return test_config
    
    def _create_run_set_folder(self):
        """
            here we will set the path for storing the iteration logs. We are re-using the directories created by mobly framework
        mobly will create a runset id and folder like '03-19-2024_12-36-26-432'
        iteration wise data will be stored in the directory <log_path>/MatterTest/<run-set>/<test_case_name>
        if this path does not exist then current directory will be used.

        self.root_output_path -> created by mobly will have structure of <log_path>/MatterTest/<run-set>
                self.TAG -> created by mobly will have test_class_name
        """
        run_set_folder_path = os.path.join(self.root_output_path, self.TAG)
        if not os.path.exists(run_set_folder_path):
            run_set_folder_path = os.path.join(os.getcwd(), datetime.datetime.now().strftime("%d-%m-%Y_%H-%M-%S-%f"),
                                               self.TAG)
            os.mkdir(run_set_folder_path)
        self.test_config.runset_folder_path = run_set_folder_path
        return run_set_folder_path
    
    def _create_iteration_log_file(self,iteration_count):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # TODO : Fix the path here
        try :
            self.iter_log_path = os.path.join(self.run_set_folder, str(iteration_count))
            if not os.path.exists(self.iter_log_path):
                os.makedirs(self.iter_log_path)
            log_filename = os.path.join(self.iter_log_path, f"log_{timestamp}.log")
            self.iteration_log = self.qa_logger.create_log_file(log_filename)
            log.info("Started Iteration {}".format(iteration_count))
            self.iteration_log_created = True
            self.test_config.iter_log_path = self.iter_log_path
        except Exception as e:
            log.error("Failed to create iteration log file {e}".format(e))
            sys.exit(1)
        
    def _get_dut_obj(self):
        module = self._import_platorm()
        return self._create_dut_obj(module)
    
    def _import_platorm(self):
        try:
            platform = self.test_config.general_configs.platform_execution
            if hasattr(self.test_config.dut_config,platform):
                dut_platform = getattr(self.test_config.dut_config, platform)
                # import platform specific module
                module = importlib.import_module(dut_platform.module)
                return module
            else:
                log.error("DUT module not available")
                sys.exit()
        except Exception as e:
            logging.error("Error loading dut module: {}".format(e))
            traceback.print_exc()
            sys.exit()

    def _create_dut_obj(self,module):
        return module.create_dut_object(self.test_config)
    
    def pre_iteration(self):
        """
        On begining of each iteration , make analytics dic to null and test result to fail
        """
        self.analytics_dict = {}
        self.iteration_test_result = TestResultEnums.TEST_RESULT_FAIL
        if not self.iteration_log_created:
            self._create_iteration_log_file(self.current_iteration)
        self.dut.pre_iteration_loop()
   
        # TODO remove
        #iteration_result_record = {(iteration_data, iteration_tc_execution_data)}
        iteration_result_record = {IterationTestResultsEnums.RECORD_ITERATION_NUMBER: self.current_iteration, (IterationTestResultsEnums.RECORD_ITERATION_DATA, IterationTestResultsEnums.RECORD_ITERATION_TC_EXECUTION_DATA, 
                                    IterationTestResultsEnums.RECORD_ITERATION_BEGIN_TIME):datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")}

        self.test_results_record.test_iteration_result_record.update_record(iteration_result_record)

    def _create_iteration_json_file(self, iteration_record=None):
            iteration_json_file = os.path.join(self.iter_log_path, "iteration.json")
            with open(iteration_json_file, 'w') as file_write:
                json.dump(iteration_record, file_write, indent=4)

    def post_iteration(self):
        self.dut.post_iteration_loop()
        log.info("Iteration {} {} :".format(self.current_iteration, self.iteration_test_result))
        self.qa_logger.close_log_file(self.iteration_log)
        # set this flag to create log in next iteration
        self.iteration_log_created = False

        if self.iteration_test_result == IterationTestResultsEnums.RECORD_ITERATION_RESULT_PASS:
            self.total_number_of_iterations_passed = self.total_number_of_iterations_passed + 1
        else:
            self.total_number_of_iterations_failed = self.total_number_of_iterations_failed + 1
            self.list_of_iterations_failed.append(self.current_iteration)
            log.info("Iterations Failed so far {}".format(self.list_of_iterations_failed))
        
        #update iteration result, end time
        iteration_result_record = {(IterationTestResultsEnums.RECORD_ITERATION_DATA, IterationTestResultsEnums.RECORD_ITERATION_TC_EXECUTION_DATA, 
                                    IterationTestResultsEnums.RECORD_ITERATION_END_TIME):datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                                    (IterationTestResultsEnums.RECORD_ITERATION_DATA, IterationTestResultsEnums.RECORD_ITERATION_TC_EXECUTION_DATA,
                                     IterationTestResultsEnums.RECORD_ITERATION_RESULT):self.iteration_test_result,
                                     (IterationTestResultsEnums.RECORD_ITERATION_DATA,IterationTestResultsEnums.RECORD_ITERATION_TC_ANALYTICS_DATA)
                                     :self.analytics_dict
                                    }
        if self.iteration_test_result != TestResultEnums.TEST_RESULT_PASS:
            iteration_result_record.update({(IterationTestResultsEnums.RECORD_ITERATION_DATA, IterationTestResultsEnums.RECORD_ITERATION_TC_EXECUTION_DATA, 
                                             IterationTestResultsEnums.RECORD_ITERATION_EXCEPTION):self.iteration_exception})
            
        #TODO handle how to send exception data in the iteration record, now I am not appending that.
        self.test_results_record.test_iteration_result_record.update_record(iteration_result_record)
        self._create_iteration_json_file(self.test_results_record.test_iteration_result_record.record)

        #TODO attach analytics dictionry also to the iteration_result_record
        
        summary_record = { SummaryTestResultsEnums.RECORD_NUMBER_OF_ITERATIONS_COMPLETED : self.current_iteration,
                            SummaryTestResultsEnums.RECORD_NUMBER_OF_ITERATIONS_PASSED : self.total_number_of_iterations_passed,
                          SummaryTestResultsEnums.RECORD_NUMBER_OF_ITERATIONS_FAILED : self.total_number_of_iterations_failed,
                          SummaryTestResultsEnums.RECORD_LIST_OF_ITERATIONS_FAILED : self.list_of_iterations_failed
                        }
        self.test_results_record.summary_result_record.update_record(summary_record)        
        self.test_result_observable.notify(self.test_results_record)
    
        #TODO, reset the iteration record result data

    def end_of_test(self, *args):
        print("I am in base class end of test ")
        summary_record = {SummaryTestResultsEnums.RECORD_TEST_STATUS: SummaryTestResultsEnums.RECORD_TEST_COMPLETED, 
                          SummaryTestResultsEnums.RECORD_TEST_END_TIME : datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
        self.test_results_record.summary_result_record.update_record(summary_record)
        self.test_result_observable.notify(self.test_results_record)
    
    def iterate_tc(iterations=1):
        def decorator(func):
            async def wrapper(self, *args, **kwargs):
                print("Decorator parameter:", iterations)
                fetched_dut_info = False
                for current_iteration in range(1,iterations+1):
                    self.current_iteration = current_iteration
                    self.pre_iteration()
                    self.test_config.current_iteration = self.current_iteration
                    try:
                        result = await func(*args, **kwargs)
                        iteration_test_result = TestResultEnums.TEST_RESULT_PASS
                        self.update_analytics()
                    except IterationError as e:
                        print("I got exception, failed iteration {}".format(current_iteration))
                        logging.error(e, exc_info=True)
                        self.update_iteration_logs()
                        iteration_test_result = TestResultEnums.TEST_RESULT_FAIL
                        #return result# you dont need this
                    self.post_iteration()
                self.end_of_test()
            return wrapper
        return decorator

    async def fetch_analytics_from_dut(self, dev_ctrl: ChipDeviceCtrl = None, node_id: int = None, endpoint: int = 0):
        if self.fetch_dut_info_once_status is True:
            await self._fetch_dut_info_once()
            self.fetch_dut_info_once_status = False

        if dev_ctrl is None:
            dev_ctrl = self.default_controller
        if node_id is None:
            node_id = self.dut_node_id

        analytics_params = getattr(self.test_config.general_configs,"analytics_parameters")
        if analytics_params is not None:
            # analytics_params is python oject so read attributes using vars
            analytics_params_dict = vars(analytics_params)
            for k,v in analytics_params_dict.items():
                #get the complete structure of one single analytics
                alaytics_struct = v
                # split the attribute of the analytics to get class instance of attribute 
                components = alaytics_struct.attribute.split('.')
                root = Clusters
                for component in components:
                    root = getattr(root,component)
                try :
                    response = await self.read_single_attribute(dev_ctrl=dev_ctrl,node_id=node_id,
                                            endpoint= alaytics_struct.end_point,
                                                attribute = root)
                except Exception as e :
                    log.error("Read attribute function timedout : {}".format(e))
                    self.iteration_exception = str(e)
                    response = {}

                self.analytics_dict.update({k:response})
    
    async def _fetch_dut_info_once(self, dev_ctrl: ChipDeviceCtrl = None, node_id: int = None, endpoint: int = 0):
        if dev_ctrl is None:
            dev_ctrl = self.default_controller
        if node_id is None:
            node_id = self.dut_node_id

        default_info_attributes = {DUTInformationRecordEnums.RECORD_PRODUCT_NAME: Clusters.BasicInformation.Attributes.ProductName,
                                    DUTInformationRecordEnums.RECORD_VENDOR_NAME: Clusters.BasicInformation.Attributes.VendorName,
                                    DUTInformationRecordEnums.RECORD_VENDOR_ID: Clusters.BasicInformation.Attributes.VendorID,
                                    DUTInformationRecordEnums.RECORD_HARDWARE_VERSION: Clusters.BasicInformation.Attributes.HardwareVersionString,
                                    DUTInformationRecordEnums.RECORD_SOFTWARE_VERSION: Clusters.BasicInformation.Attributes.SoftwareVersionString,
                                    DUTInformationRecordEnums.RECORD_PRODUCT_ID: Clusters.BasicInformation.Attributes.ProductID}
        dut_info_recorded = {}
        for k,v in default_info_attributes.items():
            try :
                response = await self.read_single_attribute(dev_ctrl=dev_ctrl,node_id=node_id,
                                        endpoint= 0,
                                        attribute = v)
            except Exception as e :
                    log.error("Read attribute function timedout : {}".format(e))
                    self.iteration_exception = str(e)
                    response = {}
            dut_info_recorded.update({k: response})
        self.test_results_record.device_information_record.update_record(dut_info_recorded)

    def update_iteration_logs(self):
        pass

    def pair_dut(self) -> bool:
        try:
            # TODO pass list idx as 0 for now as we are using default nodeID _DEFAULT_DUT_NODE_ID
            if self._commission_device(0):
                return True
        except Exception as e:
            pairing_result = {"status": "failed", "failed_reason": str(e)}
            tb = traceback.format_exc()
            raise TestCaseError(pairing_result,tb)
     
    
    def unpair_dut(self, controller=None, node_id=None) -> dict:
        try:
            if controller is None and node_id is None:
                controller = self.default_controller
                node_id = self.dut_node_id

            controller.UnpairDevice(node_id)
            time.sleep(3)
            controller.ExpireSessions(node_id)
            time.sleep(3)
            log.info("unpair_dut completed successfully")
            return True

        except Exception as e:
            logging.error(e, exc_info=True)
            unpair_result = {"status": "failed", "failed_reason": e.msg}
            if isinstance(e, chip.exceptions.ChipStackError):
                #TODO handle this properly -- Check
                unpair_result = {"status": "failed", "failed_reason": e.msg}
            tb = traceback.format_exc()
            raise TestCaseError(unpair_result,tb)


dut_objects_list = []