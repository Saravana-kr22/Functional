from mobly.records import TestResultEnums, TestResultRecord, ExceptionRecord
import mobly.utils as utils
from enum import Enum, auto

class ResultsRecordTypeEnums:
    SummaryRecordType = "test_summary_record"
    DUTNodeInformationRecordType = "dut_information_record"
    IterationRecordType = "iteration_record"
class DUTInformationRecordEnums:
    RECORD_VENDOR_NAME  = "vendor_name"
    RECORD_PRODUCT_NAME = "product_name"
    RECORD_PRODUCT_ID   = "product_id"
    RECORD_VENDOR_ID    = "vendor_id"
    RECORD_SOFTWARE_VERSION = "software_version"
    RECORD_HARDWARE_VERSION = "hardware_version"

class DUTInformationRecord:
    def __init__(self) -> None:
        self.record_dict = {}
        self.record_dict[DUTInformationRecordEnums.RECORD_VENDOR_NAME] = None
        self.record_dict[DUTInformationRecordEnums.RECORD_PRODUCT_NAME] = None
        self.record_dict[DUTInformationRecordEnums.RECORD_PRODUCT_ID] = None
        self.record_dict[DUTInformationRecordEnums.RECORD_VENDOR_ID] = None
        self.record_dict[DUTInformationRecordEnums.RECORD_SOFTWARE_VERSION] = None
        self.record_dict[DUTInformationRecordEnums.RECORD_HARDWARE_VERSION] = None
        self.record = {}
        self.record.update({ResultsRecordTypeEnums.DUTNodeInformationRecordType: self.record_dict})

    def update_record(self, record_dict=None):
        for k, v in record_dict.items():
            self.record[ResultsRecordTypeEnums.DUTNodeInformationRecordType][k] = v

class SummaryTestResultsEnums:
    RECORD_TEST_NAME = "test_case_name"
    RECORD_TEST_CASE_ID = "test_case_id"
    RECORD_TEST_CLASS = "test_case_class"
    RECORD_TEST_BEGIN_TIME = "test_case_begined_at"
    RECORD_TEST_END_TIME = "test_case_ended_at"
    RECORD_TEST_STATUS = "test_case_status"
    RECORD_TEST_COMPLETED = "Test Completed"
    RECORD_TEST_IN_PROGRESS = "Test In Progress"
    RECORD_TOTAL_NUMBER_OF_ITERATIONS = "total_number_of_iterations"
    RECORD_NUMBER_OF_ITERATIONS_COMPLETED = "number_of_iterations_completed"
    RECORD_NUMBER_OF_ITERATIONS_PASSED = "number_of_iterations_passed"
    RECORD_NUMBER_OF_ITERATIONS_FAILED = "number_of_iterations_failed"
    RECORD_LIST_OF_ITERATIONS_FAILED = "list_of_iterations_failed"
    RECORD_PLATFORM = "platform"
    RECORD_COMMISSIONING_METHOD = "commissioning-method"
    RECORD_ANALYTICS_METADATA = "analytics_parameters"
 
                
class SummaryTestResultRecord:
    def __init__(self, **kwargs):
        record_dict = {}
        kwargs_dict = kwargs.get('summary_record')
        record_dict[SummaryTestResultsEnums.RECORD_TEST_NAME] = kwargs_dict.get(SummaryTestResultsEnums.RECORD_TEST_NAME)
        record_dict[SummaryTestResultsEnums.RECORD_TEST_CASE_ID] = kwargs_dict.get(SummaryTestResultsEnums.RECORD_TEST_CASE_ID)
        record_dict[SummaryTestResultsEnums.RECORD_TEST_CLASS] = kwargs_dict.get(SummaryTestResultsEnums.RECORD_TEST_CLASS)
        record_dict[SummaryTestResultsEnums.RECORD_TEST_BEGIN_TIME] = kwargs_dict.get(SummaryTestResultsEnums.RECORD_TEST_BEGIN_TIME)
        record_dict[SummaryTestResultsEnums.RECORD_TEST_END_TIME] = None
        record_dict[SummaryTestResultsEnums.RECORD_TEST_STATUS] = SummaryTestResultsEnums.RECORD_TEST_IN_PROGRESS
        record_dict[SummaryTestResultsEnums.RECORD_TOTAL_NUMBER_OF_ITERATIONS] = kwargs_dict.get(SummaryTestResultsEnums.RECORD_TOTAL_NUMBER_OF_ITERATIONS)
        record_dict[SummaryTestResultsEnums.RECORD_NUMBER_OF_ITERATIONS_COMPLETED] = None
        record_dict[SummaryTestResultsEnums.RECORD_NUMBER_OF_ITERATIONS_PASSED] = None
        record_dict[SummaryTestResultsEnums.RECORD_NUMBER_OF_ITERATIONS_FAILED] = None
        record_dict[SummaryTestResultsEnums.RECORD_PLATFORM] = kwargs_dict.get(SummaryTestResultsEnums.RECORD_PLATFORM)
        record_dict[SummaryTestResultsEnums.RECORD_COMMISSIONING_METHOD] = kwargs_dict.get(SummaryTestResultsEnums.RECORD_COMMISSIONING_METHOD)
        record_dict[SummaryTestResultsEnums.RECORD_LIST_OF_ITERATIONS_FAILED] = []
        record_dict[SummaryTestResultsEnums.RECORD_ANALYTICS_METADATA] = kwargs_dict.get(SummaryTestResultsEnums.RECORD_ANALYTICS_METADATA)
        self.record = {}
        self.record.update({ResultsRecordTypeEnums.SummaryRecordType : record_dict})

    def update_record(self,record_dict=None):
        for k,v in record_dict.items():
            self.record[ResultsRecordTypeEnums.SummaryRecordType][k] = v

class IterationTestResultsEnums:
    RECORD_ITERATION_RECORD = 'iteration_record'
    RECORD_ITERATION_NUMBER = 'iteration_number'
    RECORD_ITERATION_DATA = 'iteration_data'
    RECORD_ITERATION_TC_EXECUTION_DATA = 'iteration_tc_execution_data'
    RECORD_ITERATION_TC_ANALYTICS_DATA = 'iteration_tc_analytics_data'
    RECORD_ITERATION_BEGIN_TIME = 'iteration_begin_time'
    RECORD_ITERATION_END_TIME = 'iteration_end_time'
    RECORD_ITERATION_RESULT = 'iteration_result'
    RECORD_ITERATION_EXCEPTION = 'exception'
    RECORD_ITERATION_RESULT_PASS = 'PASS'
    RECORD_ITERATION_RESULT_FAIL = 'FAIL'
    RECORD_ITERATION_RESULT_SKIP = 'SKIP'
    RECORD_ITERATION_RESULT_ERROR = 'ERROR'
    RECORD_ITERATION_RECORD_LIST = 'list_of_iteration_records'

class IterationTestResultRecord():
    def __init__(self, iteration_number=None):

        iter_execution_data_dict = {}
        iter_execution_data_dict[IterationTestResultsEnums.RECORD_ITERATION_BEGIN_TIME] = None
        iter_execution_data_dict[IterationTestResultsEnums.RECORD_ITERATION_END_TIME] = None
        iter_execution_data_dict[IterationTestResultsEnums.RECORD_ITERATION_RESULT] = None

        iter_execution_data_record = {}
        iter_execution_data_record.update({IterationTestResultsEnums.RECORD_ITERATION_TC_EXECUTION_DATA: iter_execution_data_dict })

        iter_analytics_data_record = {}
        iter_execution_data_record.update({IterationTestResultsEnums.RECORD_ITERATION_TC_ANALYTICS_DATA: iter_analytics_data_record })

        iter_data = {}
        iter_data.update({IterationTestResultsEnums.RECORD_ITERATION_DATA: iter_execution_data_record})
        # do the same above thing for analytics data i.e.RECORD_ANALYTICS_RECORD and update that in self.iter_record something like
        #  self.iter_data.update({IterationTestResultsEnums.RECORD_ITERATION_DATA: {self.iter_data_dict, self.analytics_dict})

        record_dict = {}
        record_dict[IterationTestResultsEnums.RECORD_ITERATION_NUMBER] = None
        record_dict.update(iter_data)
        
        self.record= {}
        self.record.update({IterationTestResultsEnums.RECORD_ITERATION_RECORD: record_dict})
        
    
    def update_record(self, new_dict=None):
        """
        The new_dict can have a single key, value pair or a tuple with keys and the value, something like example
        new_dict = {"new_levl":"Test",('level1','sublevel1','analytics_125'):900, ('level2','sublevel2','analytics_5'):105}
        any new key will be inserted inside the Iteration Record value.
        """
        for k,v in new_dict.items():
            current_dict = self.record[IterationTestResultsEnums.RECORD_ITERATION_RECORD]
            if isinstance(k,tuple):
                for level in k[:-1]:
                    current_dict = current_dict.setdefault(level, {})
                current_dict[k[-1]] = v
            else:
                self.record[IterationTestResultsEnums.RECORD_ITERATION_RECORD].update({k:v})
    
    def __str__(self) -> str:
        return self._to_dict()
    
    def _to_dict(self):
        string_dict = {}
        for k,v in self.record:
            if isinstance(v,dict):
                self._to_dict(v)
            string_dict.update({k,v})
        

class TestresultsRecord():
    def __init__(self, summary_record=None, dut_record=None, iter_record=None) -> None:
        self.summary_result_record = SummaryTestResultRecord(summary_record=summary_record)
        self.device_information_record = DUTInformationRecord()
        self.test_iteration_result_record = IterationTestResultRecord()

    