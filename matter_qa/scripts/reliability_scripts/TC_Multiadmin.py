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
from matter_qa.library.helper_libs.matter_testing_support import async_test_body, default_matter_test_main , DiscoveryFilterType
from matter_qa.library.helper_libs.exceptions import TestCaseError, TestCaseExit
from matter_qa.library.base_test_classes.test_results_record import TestResultEnums


class TC_Multiadmin(MatterQABaseTestCaseClass):

    def __init__(self, *args):
        #Todo move this into some meta data
        self.tc_name = "Multi_Admin"
        self.tc_id = "stress_1_2"
        super().__init__(*args)

    def create_unique_controller_id(self, fabric):
        #To create a unquie value to each controller
        return fabric + ((self.test_config.current_iteration-1) * self.max_fabric_supported_by_dut)
    
    def create_unique_node_id(self, fabric):
        #To create a unquie node_id for each controller
        return self.dut_node_id + fabric + ((self.test_config.current_iteration-1) * self.max_fabric_supported_by_dut)

    def find_dut_node_id(self, controller_index):
        return self.dut_node_id + controller_index + ((self.test_config.current_iteration-1) * self.max_fabric_supported_by_dut)+1
    
    def build_controller_object(self, controller_id):
        # This function is used to build the controllers
        try:
            logging.info(f'Controller node id for controller-{controller_id}') 
            # This object is used to create a new empty list in CA Index
            th_certificate_authority = self.certificate_authority_manager.NewCertificateAuthority()
            th_fabric_admin = th_certificate_authority.NewFabricAdmin(vendorId=0xFFF1, fabricId= controller_id + 1)           
            controller_object = th_fabric_admin.NewController(controller_id)
            return controller_object
        # This execption will be catched if the we unable to build the controller
        except Exception as e:
            logging.error(f"Failed to build the controller for {controller_id} with error {str(e)}"
                        ,exc_info=True)
            raise TestCaseError(str(e))
            
    async def controller_pairing(self,controller_object ,nodeid, commissioning_parameters):
        try:
            logging.info('TH1 opens a commissioning window')
            #Setuppincode for the current controller
            setup_pincode = commissioning_parameters.commissioningParameters.setupPinCode
            #discriminator for the current controller
            discriminator = commissioning_parameters.randomDiscriminator
            logging.info(f'Commissioning process with DUT has been initialized')
            controller_object.ResetTestCommissioner()
            paring_result = controller_object.CommissionOnNetwork(
                            nodeId=nodeid, setupPinCode=setup_pincode,
                            filterType=DiscoveryFilterType.LONG_DISCRIMINATOR, filter=discriminator)
            
            if not paring_result.is_success:
                logging.error("Failed to pair waiting for commissioning window to close")
                raise TestCaseError(str(paring_result))
            return paring_result
        except Exception as e:
            logging.error(e, exc_info=True)
            raise TestCaseError(str(e))
        
    def decommission_the_paired_controller(self, list_of_paired_controllers):
        try: 
            for controller_object in list_of_paired_controllers:
                dut_node_id = self.find_dut_node_id(list_of_paired_controllers.index(controller_object))
                self.unpair_dut(controller_object,dut_node_id)
                controller_object.Shutdown()
        except Exception as e:
            logging.error("Failed to unpair the controller{}".format(e), exc_info=True)
            raise TestCaseExit(str(e))

    @async_test_body
    async def test_tc_multi_fabric(self):
        try:
            self.dut.factory_reset_dut()
            self.pair_dut()
        except TestCaseError as e:    
            asserts.fail("Failed to commission the TH1")
            
        @MatterQABaseTestCaseClass.iterate_tc(iterations=self.test_config.general_configs.number_of_iterations)
        async def tc_multi_fabric(*args,**kwargs):
            #List contains the controller object
            list_of_paired_controllers = []
            try:
                self.max_fabric_supported_by_dut = await self.read_single_attribute(self.default_controller, self.dut_node_id,0,
                                                        Clusters.OperationalCredentials.Attributes.SupportedFabrics)
                # Th1 is already paired using rest of the controllers
                for fabric in range(1, self.max_fabric_supported_by_dut):
                    unique_controller_id = self.create_unique_controller_id(fabric)
                    controller_object = self.build_controller_object(unique_controller_id)
                    commissioning_parameters = self.openCommissioningWindow(dev_ctrl = self.default_controller, node_id = self.dut_node_id)
                    unique_node_id = self.create_unique_node_id(fabric)
                    await self.controller_pairing(controller_object, unique_node_id ,commissioning_parameters)
                    list_of_paired_controllers.append(controller_object)
            except Exception as e:
                self.iteration_test_result == TestResultEnums.TEST_RESULT_FAIL
            self.decommission_the_paired_controller(list_of_paired_controllers)
            await self.fetch_analytics_from_dut()
                
        await tc_multi_fabric(self)
        
if __name__ == "__main__":
    default_matter_test_main(testclass=TC_Multiadmin,do_not_commision_first = True)