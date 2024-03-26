import logging
import time
import traceback
import chip.clusters as Clusters

from mobly import asserts
from chip.clusters import OperationalCredentials as opCreds
from matter_qa.library.base_test_classes.matter_qa_base_test_class import MatterQABaseTestCaseClass
from matter_qa.library.helper_libs.matter_testing_support import async_test_body, default_matter_test_main, DiscoveryFilterType
from matter_qa.library.helper_libs.exceptions import TestCaseError, IterationError, BuildControllerError
from matter_qa.library.base_test_classes.test_results_record import  TestResultEnums 

class Multi_Admin(MatterQABaseTestCaseClass):
    def __init__(self, *args):
        super().__init__(*args)
        # This variable is used to store index of the controller in the loop
        self.current_controller = 0
        try:
            self.dut.factory_reset_dut()
            self.dut.pre_testcase_loop()
            self.pair_dut()
        except TestCaseError:
            self.dut.factory_reset_dut()
            asserts.fail("Failed to commission the TH1")
        self.th1 = self.default_controller
        
    async def check_the_no_of_controllers_are_in_range(self):
        """
        This function will check that the Number of controllers given in the int-arg controller
        is less than the supporedfabrics of the DUT by reading the supported fabric from the 
        Node operational cluster """
        if self.matter_test_config.global_test_params.get("controllers"):
            self.number_of_controllers = self.matter_test_config.global_test_params.get("controllers")
            max_fabrics = await self.read_single_attribute(self.default_controller, self.dut_node_id,0,
                                                        Clusters.OperationalCredentials.Attributes.SupportedFabrics)
            # This condition will terimate the testcase if the controllers value is greater than the SupportedFabrics
            if self.number_of_controllers >= int(max_fabrics):
                self.dut.factory_reset_dut(stop_reset=True)
                asserts.fail(f"Controller should be less than the Supported_fabrics:{max_fabrics}")
        # This condition will terimate the testcase if the controllers argument is not passed to the script
        else:
            self.dut.factory_reset_dut(stop_reset=True)
            asserts.assert_true('controllers' in self.matter_test_config.global_test_params,
                            " controllers must be included on the command line in "
                            "the --int-arg flag as controllers:<Number of controllers>")
        
    def check_commissioning_window_timeout(self):
        if 'commissioning_window_timeout' in self.matter_test_config.global_test_params:
            self.commissioning_timeout = self.matter_test_config.global_test_params["commissioning_window_timeout"]
        # This condition will assign the default value of 180 to the commissioning_window_timeout if it is not passed to the script
        else:
            logging.info("int-arg commissioning_window_timeout is missing, Hence using the default timeout value 180 for opencommissioning")
            self.commissioning_timeout = 180
        if self.commissioning_timeout in range(180,901):
            pass
        # This condition will terimate the testcase if commissioning_window_timeout is out of range
        else:
            self.dut.factory_reset_dut(stop_reset=True)
            asserts.assert_less_equal(self.commissioning_timeout, 900, 
                                    f"commissioning_window_timeout value should be less than 901 seconds")
            asserts.assert_greater_equal(self.commissioning_timeout, 180, 
                                    f"commissioning_window_timeout value should be greater than 179 seconds")
            
    def build_controller(self, controller_id_itr) -> dict:
        # This function is used to build the controllers
        try:
            unique_controller_id = controller_id_itr + ((self.test_config.current_iteration-1) * int(self.number_of_controllers))
            logging.info(f'Controller node id for controller-{controller_id_itr} in {self.test_config.current_iteration} iteration is {unique_controller_id}') 
            # This object is used to create a new empty list in CA Index
            th_certificate_authority = self.certificate_authority_manager.NewCertificateAuthority()
            th_fabric_admin = th_certificate_authority.NewFabricAdmin(vendorId=0xFFF1, fabricId=self.th1.fabricId + self.current_controller + 1)           
            dut_node_id =  self.dut_node_id + unique_controller_id
            thnodeid = self.th1.nodeId + unique_controller_id
            th = th_fabric_admin.NewController(thnodeid)
            return {"status":"success", "dev_controller_dict":{"DUT_node_id": dut_node_id ,
                    "TH_node_id": thnodeid,
                    "TH_object": th,
                    "TH_CA": th_certificate_authority,
                    "TH_Name": f"Commissioner-{unique_controller_id}"}}
        # This execption will be catched if the we unable to build the controller
        except Exception as e:
            logging.error(f"Failed to build the controller {self.current_controller}in the iteration {self.test_config.current_iteration} with error {str(e)}"
                          ,exc_info=True)
            build_result = {"status":"failed", "failure_reason":str(e)} 
            tb = traceback.format_exc()
            raise BuildControllerError(build_result, tb)
        
    async def controller_pairing(self,controller_details_dict):
        try:
            dutnodeid = controller_details_dict.get("DUT_node_id")
            logging.info('TH1 opens a commissioning window')
            opencommissioning_result_dict =  self.openCommissioningWindow()
            if opencommissioning_result_dict.get("status") == "failed":
                await self.pairing_failure(opencommissioning_result_dict.get("failure_reason"))
                return opencommissioning_result_dict
            # This object stores the info about the open commissioning window like passcode, discriminator. 
            opencommissioning_object = opencommissioning_result_dict.get("commissioning_parameters")
            #Setuppincode for the current controller
            setuppincode = opencommissioning_object.commissioningParameters.setupPinCode
            #discriminator for the current controller
            discriminator = opencommissioning_object.randomDiscriminator
            logging.info(f'TH{self.current_controller} starts the commissioning with DUT')
            th = controller_details_dict.get("TH_object")
            th.ResetTestCommissioner()
            paring_result = th.CommissionOnNetwork(
                            nodeId=dutnodeid, setupPinCode=setuppincode,
                            filterType=DiscoveryFilterType.LONG_DISCRIMINATOR, filter=discriminator)
            # This condition will check for the pairing results Pass/Fail
            if not paring_result.is_success:
                await self.close_commissioning_window()
                return{"status":"failed","failure_reason":str(paring_result)}
            await self.check_nodeid_is_in_fabriclist(th, dutnodeid)
            return {"status":"Success","paring_result":paring_result}
        except Exception as e:
            logging.error(e, exc_info=True)
            return{"status":"failed","failure_reason":str(e)}

    async def check_nodeid_is_in_fabriclist(self, devCtrl, nodeId):
        # This function will check for the fabric is available in the fabric-list
        try:
            resp = await devCtrl.ReadAttribute(nodeId, [(opCreds.Attributes.Fabrics)])
            listOffabricsdescriptor = resp[0][opCreds][Clusters.OperationalCredentials.Attributes.Fabrics]
            for fabricDescriptor in listOffabricsdescriptor:
                print("Fabric Descriptor Read From the Device: ", fabricDescriptor)
                if fabricDescriptor.nodeID == nodeId:
                    return fabricDescriptor.fabricIndex
                else:
                    await self.pairing_failure("No matching Fabric-ID found in the Fabric list")
        except Exception as e:
            logging.error("Failed to read the listOffabricsdescriptor", exc_info=True)
        
    async def pairing_failure(self, error): 
        # This function is used to store the failure reason for the pairing the controller  
        if not self.test_config.general_configs.continue_excution_on_fail: 
            raise IterationError(error)
        else:
            raise TestCaseError(error)
        
    async def shutdown_all_controllers(self, list_of_controllers, list_of_paired_controller_index):
        # This function will unpair the paired controller and shutdown all the controllers that created in an iteration
        for controller_details_dict in list_of_controllers:
                self.current_controller = list_of_controllers.index(controller_details_dict) +1
                th = controller_details_dict.get("TH_object")
                th_ca = controller_details_dict.get("TH_CA")
                dutnodeid = controller_details_dict.get("DUT_node_id")
                # This condtion is used to confirm that the controller is paired to the DUT
                if dutnodeid in list_of_paired_controller_index:
                    logging.info("Unpairing the controller-{} of iteration {}"
                                 .format(self.current_controller, self.test_config.current_iteration))
                    unpair_result = self.unpair_dut(th, dutnodeid)
                    # this condition is used to check that the unpair is completed successfully
                    if unpair_result.get("status") == "failed":
                        logging.error("Failed to unpair the controller-{} in the iteration {} with the error:{}"
                                      .format(self.current_controller,self.test_config.current_iteration ,unpair_result.get("failed_reason")) 
                                      ,exc_info=True)
                        await self.unpair_failure(unpair_result.get("failed_reason"))
                try:
                    # This function is used to shutdown the controller object
                    th.Shutdown()
                    th_ca.Shutdown()
                except Exception as e:
                    logging.error(f"Failed to shutdown the controller-{self.current_controller} of the iterartion {self.test_config.current_iteration} with error:{str(e)}",
                                  exc_info= True)
    
    async def unpair_failure(self, error):
        #  This function is used to store the failure reason for the Unpairing the controller 
        if not self.test_config.general_configs.continue_excution_on_fail:
            raise IterationError(error)
        else:
            raise TestCaseError(error)
        
    async def close_commissioning_window(self):
        # This function is used to close the commissioning window if it is in open state
        try:
            revokeCmd = Clusters.AdministratorCommissioning.Commands.RevokeCommissioning()
            await self.th1.SendCommand(nodeid=self.dut_node_id, endpoint=0, payload=revokeCmd, timedRequestTimeoutMs=1000)
            time.sleep(1)
        except Exception as e:
            logging.error("Failed to close the commissioning window due to the error {}".format(e),exc_info=True) 
            time.sleep(self.commissioning_timeout)
     
    