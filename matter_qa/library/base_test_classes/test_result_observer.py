from .test_observer import Observable,Observer
from .test_results_record import IterationTestResultsEnums
import matter_qa.library.base_test_classes.test_results_record as tr
import json
import os
import logging
import sys

class TestResultObserver(Observer):
    def __init__(self, file_tc_summary):
        self.file_tc_summary = file_tc_summary

    def dispatch(self, record):
        # if file doesnt exist
        if not os.path.exists(self.file_tc_summary):
            # File doesn't exist, create it and write default data
            with open(self.file_tc_summary, 'w') as file:
                json_data = {IterationTestResultsEnums.RECORD_ITERATION_RECORD_LIST:[]}
                json_data.update(record.summary_result_record.record) 
                json_data.update(record.device_information_record.record)
                json_data[IterationTestResultsEnums.RECORD_ITERATION_RECORD_LIST].append(
                    record.test_iteration_result_record.record[IterationTestResultsEnums.RECORD_ITERATION_RECORD])
                json.dump(json_data, file, indent=4)
        else:
            with open(self.file_tc_summary, 'r') as file:
                try:
                    json_data = json.load(file)
                except Exception as e:
                    logging.info('Error loading JSON file: {}'.format(e))
                    sys.exit(1)
                summary_record = json_data[tr.ResultsRecordTypeEnums.SummaryRecordType]
                for k, v in record.summary_result_record.record[tr.ResultsRecordTypeEnums.SummaryRecordType].items():
                    summary_record[k] = v
                dev_record = json_data[tr.ResultsRecordTypeEnums.DUTNodeInformationRecordType]
                for k, v in record.device_information_record.record[tr.ResultsRecordTypeEnums.DUTNodeInformationRecordType].items():
                    dev_record[k] = v
                list_of_iterations_dict = []
                # append the test iteration result to the list of existing iterations.
                list_of_iterations_dict= json_data[tr.IterationTestResultsEnums.RECORD_ITERATION_RECORD_LIST]
                # we get only iteration record
                iteration_number = record.test_iteration_result_record.record[tr.IterationTestResultsEnums.RECORD_ITERATION_RECORD][IterationTestResultsEnums.RECORD_ITERATION_NUMBER]
                if len(list_of_iterations_dict) < iteration_number :
                    list_of_iterations_dict.append(record.test_iteration_result_record.record[IterationTestResultsEnums.RECORD_ITERATION_RECORD])
                else:
                    list_of_iterations_dict[iteration_number-1] = record.test_iteration_result_record.record[IterationTestResultsEnums.RECORD_ITERATION_RECORD]
 
                json_data[tr.ResultsRecordTypeEnums.SummaryRecordType] = summary_record
                json_data[tr.ResultsRecordTypeEnums.DUTNodeInformationRecordType] = dev_record
                json_data[tr.IterationTestResultsEnums.RECORD_ITERATION_RECORD_LIST] = list_of_iterations_dict
            
            with open(self.file_tc_summary, 'w') as file_write:
                json.dump(json_data, file_write, indent=4)