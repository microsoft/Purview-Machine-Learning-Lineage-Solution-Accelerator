def authentitae_to_purview_AML():
    from pyapacheatlas.auth import ServicePrincipalAuthentication
    from pyapacheatlas.core import PurviewClient, AtlasClassification, AtlasEntity, AtlasProcess  
    from pyapacheatlas.readers import ExcelConfiguration, ExcelReader
    from pyapacheatlas.core.util import GuidTracker
    from pyapacheatlas.core import AtlasAttributeDef, AtlasEntity, PurviewClient
    from pyapacheatlas.core.typedef import EntityTypeDef

    # get SPN details you created in step 2.1 of solution accelerator setup
    tenant_id = "<TENANT_ID>"
    client_id = "<CLIENT_ID>"
    client_secret = "<CLIENT_SECRET>"

    # get Purview account name from azure portal
    purview_name = "<PURVIEW_NAME>"

    # get AML workspace details from azure portal
    subscription_id = "<SUBSCRIPTION_ID>" 
    resource_group = "<RESOURCE_GROUP>"
    workspace_name = "<WORKSPACE_NAME>"
    workspace_region = "<WORKSPACE_REGION>"

    from pyapacheatlas.auth import ServicePrincipalAuthentication
    from pyapacheatlas.core import PurviewClient
    from pyapacheatlas.core.util import GuidTracker

    # Authenticate to your Atlas server using a Service Principal
    oauth = ServicePrincipalAuthentication(
        tenant_id= tenant_id,
        client_id= client_id,
        client_secret= client_secret
    )
    client = PurviewClient(
        account_name = purview_name,
        authentication=oauth
    )
    guid = GuidTracker()


    # get SPN details you created in step 3.1 of solution accelerator setup
    aml_client_id = "<CLIENT_ID>"
    aml_client_secret = "<CLIENT_SECRET>"
    
    
    from azureml.core.authentication import ServicePrincipalAuthentication

    sp = ServicePrincipalAuthentication(tenant_id=tenant_id, 
                                        service_principal_id=client_id, 
                                        service_principal_password=client_secret)

    from azureml.core import Workspace

    ws = Workspace.get(name=workspace_name,
                    resource_group = resource_group,
                    auth=sp,
                    subscription_id=subscription_id)
    return ws,guid,client
