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
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../../')))

from matter_qa.library.base_test_classes.matter_qa_base_test_class import MatterQABaseTestCaseClass
from matter_qa.library.helper_libs.matter_testing_support import async_test_body, default_matter_test_main
from matter_qa.library.helper_libs.exceptions import TestCaseError
from matter_qa.library.base_test_classes.test_results_record import TestresultsRecord,TestResultEnums

class TC_Pair(MatterQABaseTestCaseClass):
    def __init__(self, *args):
        #Todo move this into some meta data
        self.tc_name = "Pair_Unpair"
        self.tc_id = "stress_1_1"
        super().__init__(*args)
    
    @async_test_body
    async def test_tc_pair_unpair(self):
        self.dut.factory_reset_dut()
        @MatterQABaseTestCaseClass.iterate_tc(iterations=self.test_config.general_configs.number_of_iterations)
        async def tc_pair_unpair(*args,**kwargs):
            try:
                if self.pair_dut():  # pairing operation with DUT begins.
                    logging.info('Device has been Commissioned starting pair-unpair operation')
                    time.sleep(2)
                    await self.fetch_analytics_from_dut()
                    self.unpair_dut()  # unpair with commissioned the DUT
                    self.iteration_test_result = TestResultEnums.TEST_RESULT_PASS
                    iteration_passed = True
                self.dut.factory_reset_dut()
            except Exception as e:
                #TODO fix this properly.
                raise TestCaseError(e)
        await tc_pair_unpair(self)


if __name__ == "__main__":
    #test_start(TC_Pair.__name__)
    default_matter_test_main(testclass=TC_Pair,do_not_commision_first=True)