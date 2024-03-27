import logging
import time
import traceback

from chip.CertificateAuthority import CertificateAuthorityManager
from matter_qa.library.helper_libs.matter_testing_support import  DiscoveryFilterType
from matter_qa.library.helper_libs.exceptions import TestCaseError

def build_controller( controller_id):
    # This function is used to build the controllers
    try:
        logging.info(f'Controller node id for controller-{controller_id}') 
        # This object is used to create a new empty list in CA Index
        th_certificate_authority = CertificateAuthorityManager.NewCertificateAuthority()
        th_fabric_admin = th_certificate_authority.NewFabricAdmin(vendorId=0xFFF1, fabricId= controller_id + 1)           
        thnodeid = controller_id
        th = th_fabric_admin.NewController(thnodeid)
        return th
    # This execption will be catched if the we unable to build the controller
    except Exception as e:
        logging.error(f"Failed to build the controller for {controller_id} with error {str(e)}"
                    ,exc_info=True)
        tb = traceback.format_exc()
        raise TestCaseError(str(e), tb)
        
async def controller_pairing(th ,nodeid, commissioning_parameters):
    try:
        dutnodeid = nodeid
        logging.info('TH1 opens a commissioning window')
        #Setuppincode for the current controller
        setuppincode = commissioning_parameters.setupPinCode
        #discriminator for the current controller
        discriminator = commissioning_parameters.randomDiscriminator
        logging.info(f'Commissioning process with DUT has been initialized')
        th.ResetTestCommissioner()
        paring_result = th.CommissionOnNetwork(
                        nodeId=dutnodeid, setupPinCode=setuppincode,
                        filterType=DiscoveryFilterType.LONG_DISCRIMINATOR, filter=discriminator)
        if not paring_result.is_success:
            logging.error("Failed to pair waiting for commissioning window to close")
            time.sleep(180)
            raise TestCaseError(str(paring_result), tb)
        return paring_result
    except Exception as e:
        logging.error(e, exc_info=True)
        tb = traceback.format_exc()
        raise TestCaseError(str(e), tb)
    