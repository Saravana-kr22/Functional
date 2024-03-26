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
import gc


from matter_qa.library.base_test_classes.matter_qa_base_test_class import MatterQABaseTestCaseClass
from matter_qa.library.helper_libs.multiadmin import Multi_Admin
from matter_qa.library.helper_libs.matter_testing_support import async_test_body, default_matter_test_main
from matter_qa.library.helper_libs.exceptions import TestCaseError, BuildControllerError, IterationError

class TC_Multiadmin(Multi_Admin):

    def __init__(self, *args):
        #Todo move this into some meta data
        self.tc_name = "Multi_Admin"
        self.tc_id = "stress_1_2"
        super().__init__(*args)

    @async_test_body
    async def test_tc_multi_fabric(self):
        # For checking the number of controlers is supported by dut
        await self.check_the_no_of_controllers_are_in_range()
        # For checking the commissioning_window_timeout is in range
        self.check_commissioning_window_timeout()
        @MatterQABaseTestCaseClass.iterate_tc(iterations=self.test_config.general_configs.number_of_iterations)
        async def tc_multi_fabric(*args,**kwargs):
            try:
                list_of_controllers = []
                # Controller which are paired will be stored in this list
                list_of_paired_controller_index = []
                for controller_id_itr in range(1, int(self.number_of_controllers)+1):
                    # This condition is used to check the build controled is completed successfully
                    try:
                        controller_build_result = self.build_controller(controller_id_itr)
                    except BuildControllerError:
                        if not self.test_config.general_configs.continue_excution_on_fail:
                            #TODO needs to update after the harsith work
                            raise TestCaseError(e)
                        continue
                    controller_details_dict = controller_build_result.get("dev_controller_dict")
                    # List contains the controller objects
                    list_of_controllers.append(controller_details_dict)
                    self.current_controller =  controller_id_itr
                    paring_result_dict = await self.controller_pairing(controller_details_dict)
                    if paring_result_dict.get("status") == "failed":
                        paring_result = paring_result_dict.get("failure_reason")
                        logging.error("Failed to Commission the controller for {} in {} iteration with th error : {}"
                                    .format(list_of_controllers.index(controller_details_dict)+1,self.test_config.current_iteration, paring_result), exc_info=True)
                        await self.pairing_failure(str(paring_result))
                        continue
                    logging.info("Successfully commissioned the {}-controller of {} iteration".format(controller_id_itr, self.test_config.current_iteration))
                    # List contains the paired controllers node-id 
                    list_of_paired_controller_index.append(controller_details_dict.get("DUT_node_id"))
                await self.shutdown_all_controllers(list_of_controllers,list_of_paired_controller_index)
                gc.collect()
                # This condition will check for the result of the iteration is pass/fail
                if not list_of_paired_controller_index:
                    raise IterationError(e)        
            except Exception as e:
                #TODO fix need after harsith code
                raise IterationError(e)
            
        await tc_multi_fabric(self)
        self.dut.factory_reset_dut()
if __name__ == "__main__":
    default_matter_test_main(testclass=TC_Multiadmin,do_not_commision_first=True )