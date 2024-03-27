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
import logging
import traceback
from mobly import asserts

import chip.clusters as Clusters

from matter_qa.library.base_test_classes.matter_qa_base_test_class import MatterQABaseTestCaseClass
from matter_qa.library.helper_libs.multiadmin import build_controller, controller_pairing
from matter_qa.library.helper_libs.matter_testing_support import async_test_body, default_matter_test_main
from matter_qa.library.helper_libs.exceptions import TestCaseError, TestCaseExit
from matter_qa.library.base_test_classes.test_results_record import TestResultEnums


class TC_Multiadmin(MatterQABaseTestCaseClass):

    def __init__(self, *args):
        #Todo move this into some meta data
        self.tc_name = "Multi_Admin"
        self.tc_id = "stress_1_2"
        super().__init__(*args)

    def unique_controller_id(self, controller_id):
        return controller_id + ((self.test_config.current_iteration-1) * self.self.max_controller)

    @async_test_body
    async def test_tc_multi_fabric(self):
        try:
            self.dut.factory_reset_dut()
            self.dut.start_logging(file_name = None)
            self.pair_dut()
        except TestCaseError as e:    
            self.dut.factory_reset_dut()
            asserts.fail("Failed to commission the TH1")
            
        @MatterQABaseTestCaseClass.iterate_tc(iterations=self.test_config.general_configs.number_of_iterations)
        async def tc_multi_fabric(*args,**kwargs):
            list_of_controllers = []
            try:
                self.max_controller = await self.read_single_attribute(self.default_controller, self.dut_node_id,0,
                                                        Clusters.OperationalCredentials.Attributes.SupportedFabrics)
                for controller_id in range(1, self.max_controller):
                    th = build_controller(self.unique_controller_id(controller_id))
                    commissioning_parameters = self.openCommissioningWindow()
                    controller_pairing(th,self.unique_controller_id(controller_id),commissioning_parameters)
                    list_of_controllers.append(th)
            
            except Exception as e:
                self.iteration_test_result == TestResultEnums.TEST_RESULT_FAIL
            
            try:
                for controller in list_of_controllers:
                    self.unpair_dut(controller,self.unique_controller_id(list_of_controllers.index(controller)+1))
                    controller.Shutdown()

            except Exception as e:
                tb = traceback.format_exc()
                raise TestCaseExit(str(e), tb)
                
        await tc_multi_fabric(self, skip_restart_dut_each_iteration = True)
        self.dut.factory_reset_dut()
if __name__ == "__main__":
    default_matter_test_main(testclass=TC_Multiadmin)