import logging
import os
import sys
import time
import chip.clusters as Clusters
from mobly import asserts

from matter_qa.library.base_test_classes.matter_qa_base_test_class import MatterQABaseTestCaseClass 
from matter_qa.library.helper_libs.matter_testing_support import async_test_body, default_matter_test_main
from matter_qa.library.helper_libs.exceptions import TestCaseError, IterationError



class TC_ON_OFF(MatterQABaseTestCaseClass):
    def __init__(self, *args):
        self.tc_name = "ON_OFF"
        self.tc_id = "stress_1_3"
        super().__init__(*args)

        # For commissioning the TH1 to the dut
        try:
            self.dut.factory_reset_dut()
            self.dut.pre_testcase_loop()
            self.pair_dut()
        except TestCaseError:
            self.dut.factory_reset_dut()
            asserts.fail("Failed to commission the TH1")

    def check_cluster_status(self, after_operation_cluster_status, current_cluster_status) -> dict:
        # This function is used to check the write command is executed successfully
        if after_operation_cluster_status != current_cluster_status:
            return {"status": "success"}
        else:
            logging.info("The iteration will be failed as there is no change in cluster state after write operation")
            return {"status": "failed", "failure_reason": " No change in cluster state after write operation"}

    async def on_off_cluster_operations(self) -> dict:
        try:
            clusters = Clusters.Objects.OnOff
            # For checking the current State of On/OFF
            current_cluster_status = await self.read_single_attribute_check_success(cluster=clusters,
                                                                                    attribute=Clusters.OnOff.Attributes.OnOff,
                                                                                    endpoint=1)
            # if current_cluster_status is True then cluster is in ON state else it is OFF
            logging.info(
                f"The ON-OFF cluster's current condition is {'ON' if current_cluster_status is True else 'OFF'}")
            
            # This condition will write the oposite value of read
            if current_cluster_status is True:
                await self.default_controller.SendCommand(nodeid=self.dut_node_id, endpoint=1,
                                                          payload=Clusters.OnOff.Commands.Off())
                after_operation_cluster_status = await self.read_single_attribute_check_success(cluster=clusters,
                                                                                                attribute=Clusters.OnOff.Attributes.OnOff,
                                                                                                endpoint=1)
            else:
                await self.default_controller.SendCommand(nodeid=self.dut_node_id, endpoint=1,
                                                          payload=Clusters.OnOff.Commands.On())
                after_operation_cluster_status = await self.read_single_attribute_check_success(cluster=clusters,
                                                                                                attribute=Clusters.OnOff.Attributes.OnOff,
                                                                                                endpoint=1)
            return self.check_cluster_status(after_operation_cluster_status, current_cluster_status)
        except Exception as e:
            logging.error(e, exc_info=True)
            return {"status": "failed", "failure_reason": str(e)}

    @async_test_body
    async def test_tc_on_off(self):
        @MatterQABaseTestCaseClass.iterate_tc(iterations=self.test_config.general_configs.number_of_iterations)
        async def tc_on_off(*args,**kwargs):
            try:
                operation_result = await self.on_off_cluster_operations()
                if operation_result.get("status") == "failed":  # when the on_off cluster operation fails
                    if not self.test_config.general_configs.continue_excution_on_fail:
                            raise TestCaseError(operation_result.get("failure_reason"))
                    else:
                        raise IndentationError(operation_result.get("failure_reason"))
            except Exception as e:
                logging.error(f"Exception occurred in TC_ON_OFF.py \n exception is {e}", exc_info=True)
                raise IterationError(e)

        await tc_on_off(self)
        self.dut.factory_reset_dut()

if __name__ == "__main__":
    default_matter_test_main(testclass=TC_ON_OFF, do_not_commision_first=True)