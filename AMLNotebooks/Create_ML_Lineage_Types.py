# Copyright (c) Microsoft. All rights reserved.

# Licensed under the MIT license.

def create_ml_lineage_types(client):
    from pyapacheatlas.core.typedef import AtlasAttributeDef, EntityTypeDef, RelationshipTypeDef
    try:
        #-----------------------------------------------------------------------------------#    
        #create custom dataset type
        type_df = EntityTypeDef(
            name="custom_dataset",
            attributeDefs=[
              AtlasAttributeDef(name="format")
            ],
            superTypes = ["DataSet"]
        )
        typedef_results = client.upload_typedefs(entityDefs = [type_df], force_update=True)

        #-----------------------------------------------------------------------------------#    
        #create process with column mapping type
        type_df = EntityTypeDef(
            name="ProcessWithColumnMapping",
            attributeDefs=[
              AtlasAttributeDef(name="columnMapping")
            ],
            superTypes = ["Process"]
            )
        typedef_results = client.upload_typedefs(entityDefs = [type_df], force_update=True)

        #-----------------------------------------------------------------------------------#    
        #create AML workspace type
        type_df = EntityTypeDef(
            name="custom_ml_workspace",
            attributeDefs=[
                AtlasAttributeDef(name='name',typename='string'),
                AtlasAttributeDef(name='description',typename='string'),
                AtlasAttributeDef(name='subscription_id',typename='string'),
                AtlasAttributeDef(name='resource_group',typename='string')
            ],
            superTypes = ["DataSet"]
        )
        typedef_results = client.upload_typedefs(entityDefs = [type_df], force_update=True)
        #-----------------------------------------------------------------------------------#        
        #create types for datastore and dataset

        #create AML datastore type
        datastore_type_df = EntityTypeDef(
            name="custom_ml_datastore",
            attributeDefs=[
              AtlasAttributeDef(name="name",typename='string'),
              AtlasAttributeDef(name='container_name',typename='string'),
              AtlasAttributeDef(name='account_name',typename='string'),
              AtlasAttributeDef(name='protocol',typename='string'),
              AtlasAttributeDef(name='endpoint',typename='string'),
              AtlasAttributeDef(name='server_name',typename='string'),
              AtlasAttributeDef(name='database_name',typename='string'),
              AtlasAttributeDef(name="createdby",typename='string')
            ],
            superTypes = ["DataSet"],
            options = {"schemaElementAttribute":"dataset"}
        )

        #create AML dataset type
        dataset_type_df = EntityTypeDef(
            name="custom_ml_dataset",
            attributeDefs=[
              AtlasAttributeDef(name="name",typename='string'),
              AtlasAttributeDef(name="description",typename='string'),
              AtlasAttributeDef(name="createdby",typename='string'),
              AtlasAttributeDef(name="createdtime",typename='string')
            ],
            superTypes = ["DataSet"]
        )

        # create relationsip between datastore and dataset
        dataset_to_datastore_relationship = RelationshipTypeDef(
            name="custom_ml_datastore_to_dataset",
            relationshipCategory="COMPOSITION",
            endDef1={
                    "type": "custom_ml_datastore",
                    "name": "dataset",
                    "isContainer": True,
                    "cardinality": "SET",
                    "isLegacyAttribute": False
                },
            endDef2={
                    "type": "custom_ml_dataset",
                    "name": "datastore",
                    "isContainer": False,
                    "cardinality": "SINGLE",
                    "isLegacyAttribute": False
                }
            )

        typedef_results = client.upload_typedefs(
            entityDefs = [datastore_type_df, dataset_type_df],
            relationshipDefs = [dataset_to_datastore_relationship],
            force_update=True
        )
        #-----------------------------------------------------------------------------------# 
        #create types for experiment and experimentstep

        #create process for Ml Experiment Step
        exp_type_df = EntityTypeDef(
            name="custom_ml_experiment",
            attributeDefs=[
              AtlasAttributeDef(name='name',typename='string'),
              AtlasAttributeDef(name='notes',typename='string'),
              AtlasAttributeDef(name="createdby",typename='string'),
              AtlasAttributeDef(name="createdtime",typename='string')
            ],
            superTypes = ["Process"]
        )

        #create process for Ml Experiment Step
        exp_step_type_df = EntityTypeDef(
            name="custom_ml_experiment_step",
            attributeDefs=[
              AtlasAttributeDef(name='notes',typename='string')
            ],
            superTypes = ["Process"]
        )

        # create relationsip between experiment and experimentstep
        step_to_exp_relationship = RelationshipTypeDef(
            name="custom_ml_experiment_to_experimentstep",
            relationshipCategory="COMPOSITION",
            endDef1={
                    "type": "custom_ml_experiment",
                    "name": "experimentstep",
                    "isContainer": True,
                    "cardinality": "SET",
                    "isLegacyAttribute": False
                },
            endDef2={
                    "type": "custom_ml_experiment_step",
                    "name": "experiment",
                    "isContainer": False,
                    "cardinality": "SINGLE",
                    "isLegacyAttribute": False
                }
        )

        typedef_results = client.upload_typedefs(
            entityDefs = [exp_type_df, exp_step_type_df],
            relationshipDefs = [step_to_exp_relationship],
            force_update=True
        )
        #-----------------------------------------------------------------------------------# 

        rd = RelationshipTypeDef(
          name="custom_ml_workspace_datastore",
          attributeDefs=[],
          relationshipCategory="COMPOSITION", # Means the child can't exist  without the parent
          endDef1={ # endDef1 decribes what the parent will have as an attribute
              "type":"custom_ml_workspace", # Type of the parent
              "name":"datastores", # What the parent will have
              "isContainer": True,
              "cardinality":"SET", # This is related to the cardinality, in this case the parent Server will have a SET of Models.
              "isLegacyAttribute":False
          },
          endDef2={ # endDef2 decribes what the child will have as an attribute
              "type":"custom_ml_datastore", # Type of the child
              "name":"workspace", # What the child will have
              "isContainer":False,
              "cardinality":"SINGLE",
              "isLegacyAttribute":False
          }
        )
        client.upload_typedefs(relationshipDefs=[rd])

        #-----------------------------------------------------------------------------------#  
        rd = RelationshipTypeDef(
          name="custom_ml_workspace_experiment",
          attributeDefs=[],
          relationshipCategory="COMPOSITION", # Means the child can't exist  without the parent
          endDef1={ # endDef1 decribes what the parent will have as an attribute
              "type":"custom_ml_workspace", # Type of the parent
              "name":"experiments", # What the parent will have
              "isContainer": True,
              "cardinality":"SET", # This is related to the cardinality, in this case the parent Server will have a SET of Models.
              "isLegacyAttribute":False
          },
          endDef2={ # endDef2 decribes what the child will have as an attribute
              "type":"custom_ml_experiment", # Type of the child
              "name":"workspace", # What the child will have
              "isContainer":False,
              "cardinality":"SINGLE",
              "isLegacyAttribute":False
          }
        )
        client.upload_typedefs(relationshipDefs=[rd])

        #-----------------------------------------------------------------------------------# 
        #create types for packages and package

        #create packages type
        packages_type_df = EntityTypeDef(
            name="custom_ml_packages",
            attributeDefs=[
                AtlasAttributeDef(name='notes',typename='string')
            ],
            superTypes = ["DataSet"],
            options = {"schemaElementAttribute":"package"}
        )

        package_type_df = EntityTypeDef(
            name="custom_ml_package",
            attributeDefs=[
                AtlasAttributeDef(name='programming_language',typename='string'),
                AtlasAttributeDef(name='package_name',typename='string'),
                AtlasAttributeDef(name='version',typename='string'),
                AtlasAttributeDef(name='notes',typename='string')
            ],
            superTypes = ["DataSet"]
        )

        # create relationsip between packages and package
        package_to_packages_relationship = RelationshipTypeDef(
            name="custom_ml_packages_to_package",
            relationshipCategory="COMPOSITION",
            endDef1={
                    "type": "custom_ml_packages",
                    "name": "package",
                    "isContainer": True,
                    "cardinality": "SET",
                    "isLegacyAttribute": False
                },
            endDef2={
                    "type": "custom_ml_package",
                    "name": "packages",
                    "isContainer": False,
                    "cardinality": "SINGLE",
                    "isLegacyAttribute": False
                }
        )

        typedef_results = client.upload_typedefs(
            entityDefs = [packages_type_df, package_type_df],
            relationshipDefs = [package_to_packages_relationship],
            force_update=True
        )
      #-----------------------------------------------------------------------------------# 

        #create experiemnt config type
        type_df = EntityTypeDef(
            name="custom_ml_exp_config",
            attributeDefs=[
                AtlasAttributeDef(name='task_type',typename='string'),
                AtlasAttributeDef(name='enable_early_stopping',typename='bool'),
                AtlasAttributeDef(name='experiment_timeout_minutes',typename='int'),
                AtlasAttributeDef(name='primary_metric',typename='string'),
                AtlasAttributeDef(name='compute_target',typename='string'),
                AtlasAttributeDef(name='label_column_name',typename='string'),
                AtlasAttributeDef(name='n_cross_validations',typename='int'),
                AtlasAttributeDef(name='model_explainability',typename='bool')
            ],
            superTypes = ["DataSet"]
        )
        typedef_results = client.upload_typedefs(entityDefs = [type_df], force_update=True)

        #-----------------------------------------------------------------------------------# 

        #create model metrics type
        type_df = EntityTypeDef(
            name="custom_ml_model_metrics",
            attributeDefs=[
                AtlasAttributeDef(name='AUC',typename='float'),
                AtlasAttributeDef(name='Accuracy',typename='float'),
                AtlasAttributeDef(name='Precision',typename='float'),
                AtlasAttributeDef(name='Recall',typename='float'),
                AtlasAttributeDef(name='F1',typename='float')
            ],
            superTypes = ["DataSet"]
        )
        typedef_results = client.upload_typedefs(entityDefs = [type_df], force_update=True)

        #-----------------------------------------------------------------------------------# 

        #create model type
        type_df = EntityTypeDef(
            name="custom_ml_model",
            attributeDefs=[
                AtlasAttributeDef(name='workspace_name',typename='string'),
                AtlasAttributeDef(name='workspace_subscription_id',typename='string'),
                AtlasAttributeDef(name='workspace_resource_group',typename='string'),
                AtlasAttributeDef(name='name',typename='string'),
                AtlasAttributeDef(name='id',typename='string'),
                AtlasAttributeDef(name='version',typename='string'),
                AtlasAttributeDef(name='tags',typename='string'),
                AtlasAttributeDef(name='properties',typename='string')
            ],
            superTypes = ["DataSet"]
        )
        typedef_results = client.upload_typedefs(entityDefs = [type_df], force_update=True)

        #-----------------------------------------------------------------------------------# 

        #create endpoint type
        type_df = EntityTypeDef(
            name="custom_ml_model_endpoint",
            attributeDefs=[
                  AtlasAttributeDef(name='workspace_name',typename='string'),
                  AtlasAttributeDef(name='workspace_subscription_id',typename='string'),
                  AtlasAttributeDef(name='workspace_resource_group',typename='string'),
                  AtlasAttributeDef(name='name',typename='string'),
                  AtlasAttributeDef(name='image_id',typename='string'),
                  AtlasAttributeDef(name='compute_type',typename='string'),
                  AtlasAttributeDef(name='state',typename='string'),
                  AtlasAttributeDef(name='scoring_uri',typename='string'),
                  AtlasAttributeDef(name='tags',typename='string'),
                  AtlasAttributeDef(name='state',typename='string'),
                  AtlasAttributeDef(name='properties',typename='string'),
                  AtlasAttributeDef(name='created_by',typename='string'),
                  AtlasAttributeDef(name='sample_json',typename='string')
            ],
            superTypes = ["DataSet"]
        )
        typedef_results = client.upload_typedefs(entityDefs = [type_df], force_update=True)

        #-----------------------------------------------------------------------------------# 
    except:
        print('types already created')  

