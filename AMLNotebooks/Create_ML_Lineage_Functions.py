# +
# Copyright (c) Microsoft. All rights reserved.

# Licensed under the MIT license.

from pyapacheatlas.auth import ServicePrincipalAuthentication
from pyapacheatlas.core import PurviewClient, AtlasClassification, AtlasEntity, AtlasProcess  
from pyapacheatlas.readers import ExcelConfiguration, ExcelReader
from pyapacheatlas.core.util import GuidTracker
from pyapacheatlas.core import AtlasAttributeDef, AtlasEntity, PurviewClient
from pyapacheatlas.core.typedef import EntityTypeDef

from Authenticate_to_Purview_AML import *
ws,guid,client = authentitae_to_purview_AML()

def get_entity_details(qualifiedName,typeName):
    entities = client.get_entity(
        qualifiedName=[qualifiedName],
        typeName=typeName
    )
    for entity in entities.get("entities"):
        entity = entity
        break
    return entity
#get_entity_details('https://sampledataadls.dfs.core.windows.net/masterdata/employees.csv','azure_datalake_gen2_path')

def get_entity_guid(qualifiedName,typeName):
    entities = client.get_entity(
        qualifiedName=[qualifiedName],
        typeName=typeName
    )
    for entity in entities.get("entities"):
        entity_guid = entity.get("guid")
        break
    return entity_guid
#get_entity_guid('https://sampledataadls.dfs.core.windows.net/creditriskdata/borrower.csv','azure_datalake_gen2_path')

def get_entity_schema(guid):
    columns = []
    results = client.get_entity(guid)
    for entity in results["entities"]:
        if "tabular_schema" in entity["relationshipAttributes"]:
            ts = entity["relationshipAttributes"]["tabular_schema"]
            ts_entity = client.get_entity(ts["guid"])
            for schema in ts_entity["entities"]:
                for col in schema["relationshipAttributes"]["columns"]:
                    if col['displayText'] != ':csv':
                        columns.append(col['displayText'])
    return(columns)
    
# ent_guid = 'a8698a33-9174-43cb-8835-26968862e2bf'
# get_entity_schema(ent_guid)

def create_data_entity_with_schema_and_parent(df_data,entityname,entitytype='custom_ml_dataset',parent_entityname=None,parent_entitytype='custom_ml_datastore'):
    # Create an asset for the output data schema.
    output_schema_entity = AtlasEntity(
    name="schema-" + entityname,
    qualified_name = "pyapacheatlas://"+"schema-" + entityname,
    typeName="tabular_schema",
    guid=guid.get_guid()
    )

    df_data_schema = pd.DataFrame(list(zip(list(df_data.columns), list(df_data.dtypes))),columns=['column','dtype'])

    #Iterate over the out data frame's columns and create entities
    output_entity_schema_columns = []
    #for column in df.schema:
    for index, row in df_data_schema.iterrows():  
        temp_column = AtlasEntity(
            name = row.column,
            typeName = "column",
            qualified_name = "pyapacheatlas://schema-" + entityname + "#" + row.column,
            guid=guid.get_guid(),
            attributes = {"type":str(row.dtype),"description": row.column},
            relationshipAttributes = {"composeSchema":output_schema_entity.to_json(minimum=True)}
        )
        output_entity_schema_columns.append(temp_column)


    if parent_entityname:
        dstore_entity = get_entity_details("pyapacheatlas://"+parent_entityname, parent_entitytype)
        # Create a entity for dataset 
        dataset_output_entity = AtlasEntity(
            name=entityname,
            typeName=entitytype,
            qualified_name="pyapacheatlas://" + entityname,
            guid = guid.get_guid(),
            relationshipAttributes = {
                "tabular_schema": output_schema_entity.to_json(minimum=True),
                "datastore":dstore_entity
            }
        )
    else:
        # Create a entity for dataset 
        dataset_output_entity = AtlasEntity(
            name=entityname,
            typeName=entitytype,
            qualified_name="pyapacheatlas://" + entityname,
            guid = guid.get_guid(),
            relationshipAttributes = {
                "tabular_schema": output_schema_entity.to_json(minimum=True)
            }
        )

    # Prepare all the entities as a batch to be uploaded.
    batch = [dataset_output_entity, output_schema_entity] + output_entity_schema_columns
    batch

    # Upload all entities!
    client.upload_entities(batch=batch)
    
def create_data_entity_with_schema(df_data,entityname,entitytype='custom_ml_dataset'):
    # Create an asset for the output data schema.
    output_schema_entity = AtlasEntity(
    name="schema-" + entityname,
    qualified_name = "pyapacheatlas://"+"schema-" + entityname,
    typeName="tabular_schema",
    guid=guid.get_guid()
    )

    df_data_schema = pd.DataFrame(list(zip(list(df_data.columns), list(df_data.dtypes))),columns=['column','dtype'])

    #Iterate over the out data frame's columns and create entities
    output_entity_schema_columns = []
    #for column in df.schema:
    for index, row in df_data_schema.iterrows():  
        temp_column = AtlasEntity(
            name = row.column,
            typeName = "column",
            qualified_name = "pyapacheatlas://schema-" + entityname + "#" + row.column,
            guid=guid.get_guid(),
            attributes = {"type":str(row.dtype),"description": row.column},
            relationshipAttributes = {"composeSchema":output_schema_entity.to_json(minimum=True)}
        )
        output_entity_schema_columns.append(temp_column)

    # Create a entity for dataset 
    dataset_output_entity = AtlasEntity(
        name=entityname,
        typeName=entitytype,
        qualified_name="pyapacheatlas://" + entityname,
        guid = guid.get_guid(),
        relationshipAttributes = {
            "tabular_schema": output_schema_entity.to_json(minimum=True)
        }
    )

    # Prepare all the entities as a batch to be uploaded.
    batch = [dataset_output_entity, output_schema_entity] + output_entity_schema_columns
    batch

    # Upload all entities!
    client.upload_entities(batch=batch)
    
def create_lineage_for_entities(experimentname,processname,in_ent_qns,out_ent_qns,process_type_name='Process',ColumnMapping=False):
    # create a process 
    # inputs: list of (entity,type) tuples
    # outputs: list of (entity,type) tuples

    from pyapacheatlas.core import AtlasProcess

    in_ent_guids = []
    for in_ent_qn in in_ent_qns:
        #print(in_ent_qn,in_ent_qns[in_ent_qn])
        in_ent_guid = get_entity_guid(in_ent_qn,in_ent_qns[in_ent_qn])
        in_ent_guids.append({'guid':in_ent_guid})
    
    out_ent_guids = []
    for out_ent_qn in out_ent_qns:
        #print(in_ent_qn,in_ent_qns[in_ent_qn])
        out_ent_guid = get_entity_guid(out_ent_qn,out_ent_qns[out_ent_qn])
        out_ent_guids.append({'guid':out_ent_guid})

    process_name = experimentname + processname
    process_qn = "pyapacheatlas://" + process_name

    if ColumnMapping == False:
        process_type_name = process_type_name

        process = AtlasProcess(
            name=process_name,
            typeName=process_type_name,
            qualified_name=process_qn,
            inputs = in_ent_guids,
            outputs = out_ent_guids,
            guid=guid.get_guid()
        )
    else:
        process_type_name = "ProcessWithColumnMapping"

        column_mapping_attributes = []
        for in_ent_qn in in_ent_qns:
            cl_mapping = []
            in_ent_columns = get_entity_schema(get_entity_guid(in_ent_qn,in_ent_qns[in_ent_qn]))
            for in_col in in_ent_columns:
                cl_mapping.append({"Source":in_col,"Sink":in_col})
                #break
            mapping = {
            'DatasetMapping': {'Source':in_ent_qn,'Sink':list(out_ent_qns.keys())[0]},
            'ColumnMapping': cl_mapping
            }
            column_mapping_attributes.append(mapping)

        process = AtlasProcess(
            name=process_name,
            typeName=process_type_name,
            qualified_name=process_qn,
            inputs = in_ent_guids,
            outputs = out_ent_guids,
            guid=guid.get_guid(),
            attributes={"columnMapping":json.dumps(column_mapping_attributes)}
        )

    # Prepare all the entities as a batch to be uploaded.
    batch = [process]
    batch

    # Upload all entities!
    client.upload_entities(batch=batch)
    
def create_entity(name,typeName,config_attibutes):
    # Create an entity
    name = name 
    qn = "pyapacheatlas://" + name

    exp_config_entity = AtlasEntity(
        name=name,
        typeName=typeName,
        qualified_name=qn,
        guid = guid.get_guid(),
        attributes = config_attibutes
    )

    # Upload all entities!
    client.upload_entities(batch=[exp_config_entity.to_json()])

        
def get_dataset_details(indataset,experiment_name=''):
    result = []
    #print(indataset)
    if 'FileDataset' in str(type((indataset))):
        dssource = eval(json.loads(str(indataset).replace('FileDataset',''))['source'][0])
        sourcestore = dssource[0]
        sourcepath = dssource[1]
        sourcepathfiles = indataset.to_path()
        for sourcepathfile in sourcepathfiles:
            entityname = sourcepath.split('/')[-1] + sourcepathfile.replace('/','_') #.replace('.parquet','').replace('.csv','')
            #print('\nFileDataset:',entityname)

            dsdatastore = Datastore.get(ws, sourcestore)
            datastore_path = [DataPath(dsdatastore, sourcepath+sourcepathfile.replace('/',''))]
   
            if '.parquet' in sourcepathfile:
                tabular_dataset = Dataset.Tabular.from_parquet_files(path=datastore_path)
                df_data = tabular_dataset.take(10).to_pandas_dataframe()
                
            elif '.csv' in sourcepathfile:
                tabular_dataset = Dataset.Tabular.from_delimited_files(path=datastore_path,encoding ='iso88591') 
                #'utf8', 'iso88591', 'latin1', 'ascii', 'utf16', 'utf32', 'utf8bom' and 'windows1252'
                df_data = tabular_dataset.take(10).to_pandas_dataframe()
            
            if experiment_name != '':
                result.append((entityname + '_' + experiment_name,df_data))
            else:
                result.append((entityname,df_data))

    elif 'TabularDataset' in str(type((indataset))):
        tabular_dataset = indataset
        entityname = json.loads(str(indataset).replace('TabularDataset',''))['registration']['name']
        
        # dataset = Dataset.get_by_name(ws, name=entityname)
        # try:
        #     sourcestore = json.loads(dataset._definition)['blocks'][0]['arguments']['datastore']['datastoreName']
        # except:
        #     sourcestore = json.loads(dataset._definition)['blocks'][0]['arguments']['datastores'][0]['datastoreName']
        df_data = tabular_dataset.take(10).to_pandas_dataframe()
        #print('TabularDataset:', entityname)
        result.append((entityname,df_data))
    return result


from azureml.core import Experiment
from azureml.pipeline.core import PipelineRun

from azureml.core import Workspace, Datastore, Dataset
from azureml.data.datapath import DataPath
import json  
import pandas as pd

def create_aml_experiment_steps(ws,experiment_name):
    experiments_lst = Experiment.list(ws)
    for experiment in experiments_lst:
        if experiment.name == experiment_name:
            print(experiment)
            exp = Experiment(ws,experiment.name)
            for run in exp.get_runs(): 
                rundetails = run.get_details()

                if rundetails['status'] != 'Completed': #continue until we find a completed run 
                    continue
                pipeline_run = PipelineRun(exp, rundetails['runId'])

                steps = pipeline_run.get_steps()
                for step_run in steps:
                    step_run_details = step_run.get_details_with_logs()

                    #print(step_run_details['runDefinition']['script'])

                    purview_basepath = 'pyapacheatlas://'
                    in_ent_qns = {}
                    out_ent_qns = {}

                    step_name = step_run.name #step_run_details['runDefinition']['script']

                    #print('\n Input Datasets:\n')
                    for indataset in step_run_details['inputDatasets']:
                        in_result = get_dataset_details(indataset['dataset'],experiment_name)
                        #print(in_result)
                        #create entities                        
                        for in_res in in_result:
                            data_ent_name = in_res[0].strip('_')
                            create_data_entity_with_schema(in_res[1],data_ent_name,'custom_ml_dataset')
                            in_ent_qns[purview_basepath + data_ent_name] = 'custom_ml_dataset'
                        #break
                    #print('\n Output Datasets:\n')
                    for outdataset in step_run_details['outputDatasets']:
                        out_result = get_dataset_details(outdataset['dataset'],experiment_name)
                        #print(out_result)
                        #create entities
                        for out_res in out_result:
                            data_ent_name = out_res[0].strip('_')
                            create_data_entity_with_schema(out_res[1],data_ent_name,'custom_ml_dataset')
                            out_ent_qns[purview_basepath + data_ent_name] = 'custom_ml_dataset'
                        #break
                    #print(in_ent_qns,out_ent_qns)
                    create_lineage_for_entities(experiment_name + '_',step_name, in_ent_qns,out_ent_qns,process_type_name='custom_ml_experiment_step',ColumnMapping=False)
                    #break    
                
                break # break after processing one completed run
            break #after finding the experiment


#create workspace entity
def create_workspace_entities(ws):

    config_attibutes={}
    temp_column={}

    temp_column['name'] = ws.name
    config_attibutes.update(temp_column)
    temp_column['subscription_id'] = ws.subscription_id
    config_attibutes.update(temp_column)
    temp_column['resource_group'] = ws.resource_group
    config_attibutes.update(temp_column)

    create_entity(ws.name,'custom_ml_workspace',config_attibutes)
    #break

#create all datastore entities
def create_datastore_entities(ws):
    for datastore in ws.datastores.values():
        config_attibutes={}
        temp_column={}
        
        temp_column['name'] = datastore.name
        config_attibutes.update(temp_column)

        if ('AzureDataLakeGen2Datastore' in str(type(datastore))) or ('AzureBlobDatastore' in str(type(datastore))):
            temp_column['container_name'] = datastore.container_name
            config_attibutes.update(temp_column)
            temp_column['account_name'] = datastore.account_name
            config_attibutes.update(temp_column)
            temp_column['protocol'] = datastore.protocol
            config_attibutes.update(temp_column)
            temp_column['endpoint'] = datastore.endpoint
            config_attibutes.update(temp_column)
        elif 'AzureSqlDatabaseDatastore' in str(type(datastore)):
            #print('sql',datastore.server_name)
            temp_column['server_name'] = datastore.server_name
            config_attibutes.update(temp_column)
            temp_column['database_name'] = datastore.database_name
            config_attibutes.update(temp_column)
        elif 'AzureBlobDatastore' in str(type(datastore)):    
            pass

        create_entity(datastore.name,'custom_ml_datastore',config_attibutes)
        #break

    #create workspace and datastore relationship
    purview_basepath = 'pyapacheatlas://'
    for datastore in ws.datastores.values():
        relationshiptype = 'custom_ml_workspace_datastore'
        end1type = 'custom_ml_workspace'
        end2type = 'custom_ml_datastore'
        end1_qn = purview_basepath + ws.name
        end2_qn = purview_basepath + datastore.name
        try:
            create_entities_relationship(relationshiptype,end1type,end2type,end1_qn,end2_qn)
        except:
            pass # ignore if relationship exists

#create all dataset entities (with datastore as parent)
from azureml.core import Workspace, Datastore, Dataset
import pandas as pd
def create_dataset_entities(ws,parent_flag=True):
    purview_basepath = 'pyapacheatlas://'
    for dsname in ws.datasets:
        dataset = ws.datasets[dsname]
        try:
            if 'FileDataset' in str(type((dataset))):
                datasetsource = eval(json.loads(str(dataset).replace('FileDataset',''))['source'][0])[0]
            elif 'TabularDataset' in str(type((dataset))):
                datasetsource = eval(json.loads(str(dataset).replace('TabularDataset',''))['source'][0])[0]

            dsdetails = get_dataset_details(dataset)
            #print(dsdetails)
            for ds in dsdetails:
                if parent_flag == False:

                    create_data_entity_with_schema(ds[1],dsname,'custom_ml_dataset')
                    create_lineage_for_entities('',('register_' + dsname), {(purview_basepath+datasetsource):'custom_ml_datastore'},
                                                {(purview_basepath+ds[0]):'custom_ml_dataset'},ColumnMapping=False)
                else:
                    create_data_entity_with_schema_and_parent(ds[1],dsname,entitytype='custom_ml_dataset',
                                                              parent_entityname=datasetsource,parent_entitytype='custom_ml_datastore')    
        except:
            print('Error:',dsname)        
        #break
        
        
#create experiment entity
from azureml.core import Experiment

def create_experiment_entities(ws):
    for experiment in Experiment.list(ws):
        #create experiment entity
        config_attibutes={}
        temp_column={}

        temp_column['name'] = experiment.name
        config_attibutes.update(temp_column)

        create_entity(experiment.name,'custom_ml_experiment',config_attibutes)
        #break
        
        purview_basepath = 'pyapacheatlas://'

        #create experiment relationship to workspace
        relationshiptype = 'custom_ml_workspace_experiment'
        end1type = 'custom_ml_workspace'
        end2type = 'custom_ml_experiment'
        end1_qn = purview_basepath + ws.name
        end2_qn = purview_basepath + experiment.name
        try:
            create_entities_relationship(relationshiptype,end1type,end2type,end1_qn,end2_qn)
        except:
            pass # ignore if relationship exists
        
        for run in experiment.get_runs(): 
            rundetails = run.get_details()
            #print(rundetails)
            if rundetails['status'] != 'Completed': #continue until we find a completed run 
                continue
            #create experiment steps
            if rundetails['properties']['azureml.runsource'] == 'azureml.PipelineRun':
                print(experiment.name)
                create_aml_experiment_steps(ws,experiment.name)

                pipeline_run = PipelineRun(experiment, rundetails['runId'])

                steps = pipeline_run.get_steps()
                for step_run in steps:  
                    #create experiment relationship to workspace
                    relationshiptype = 'custom_ml_experiment_to_experimentstep'
                    end1type = 'custom_ml_experiment'
                    end2type = 'custom_ml_experiment_step'
                    end1_qn = purview_basepath + experiment.name
                    end2_qn = purview_basepath + experiment.name + '_' + step_run.name
                    try:
                        create_entities_relationship(relationshiptype,end1type,end2type,end1_qn,end2_qn)
                    except:
                        pass # ignore if relationship exists

            break # break after processing one completed run
        #break

def create_entities_relationship(relationshiptype,end1type,end2type,end1_qn,end2_qn):
    relationship = {}
    end1 = {}
    end2 = {}

    end1["guid"] = get_entity_guid(end1_qn,end1type)
    end1["typeName"] = end1type
    end1["uniqueAttributes"] = {"qualifiedName": end1_qn}

    end2["guid"] = get_entity_guid(end2_qn,end2type)
    end2["typeName"] = end2type
    end2["uniqueAttributes"] = {"qualifiedName": end2_qn}

    relationship["typeName"] = relationshiptype
    relationship["attributes"] = {}
    relationship["guid"] = guid.get_guid()
    relationship["provenanceType"] = 0
    relationship["end1"] = end1
    relationship["end2"] = end2
    relationship
    
    client.upload_relationship(relationship)         
       
def create_package_entities(experimentname,packageslist):
    packages_name = experimentname + '-packages' 
    packages_qn = "pyapacheatlas://" + packages_name

    # Create an asset for the packages.
    packages_entity = AtlasEntity(
        name = packages_name,
        qualified_name = packages_qn,
        typeName="custom_ml_packages",
        attributes = {"notes":"test note"},
        guid=guid.get_guid()
    )

    packages_entity.to_json(minimum=True)

    atlas_packages = []
    relationships = []
    for package in packageslist:
        package_attibutes={}
        temp_column={}
        temp_column['programming_language'] = str(package[0])
        package_attibutes.update(temp_column)
        temp_column['package_name'] = str(package[1])
        package_attibutes.update(temp_column)
        temp_column['version'] = str(package[2])
        package_attibutes.update(temp_column)
        temp_column['notes'] = str(package[3])
        package_attibutes.update(temp_column)

        # Create an entity for each package
        name = str(package[1]) #experimentname + '-package-' + package[1] 
        qn =   packages_qn + '#' + str(package[1])     #"pyapacheatlas://" + name

        package_entity = AtlasEntity(
            name= name,
            typeName="custom_ml_package",
            qualified_name=qn,
            guid = guid.get_guid(),
            attributes = package_attibutes,
            relationshipAttributes = {"packages":packages_entity.to_json(minimum=True)}
        )
        atlas_packages.append(package_entity)

    atlas_packages

    # Prepare all the entities as a batch to be uploaded.
    batch = [packages_entity] + atlas_packages
    client.upload_entities(batch=batch) 
    
def create_experiment_config_entity(ws,experiment_name,automl_run):
    # Get experiment config from AML run
    import json
    import pandas as pd
    run_properties = automl_run.get_properties()
    run_properties

    AMLSettingsJsonString = run_properties['AMLSettingsJsonString']
    AMLSettings = json.loads(AMLSettingsJsonString)

    df_config = pd.DataFrame(list(AMLSettings.items()),columns = ['key','value']) 

    keys = ['task_type','enable_early_stopping','experiment_timeout_minutes','primary_metric','compute_target','label_column_name','n_cross_validations','model_explainability']

    df_config = df_config[df_config['key'].isin(keys)]

    dict_config = df_config.to_dict(orient = 'records')
    dict_config

    config_attibutes={}
    for attibutes in dict_config:
        temp_column={}
        temp_column[attibutes['key']] = attibutes['value']
        config_attibutes.update(temp_column)
    config_attibutes

    # Create a entity for exp config 
    name = experiment_name + "-config"
    qn = "pyapacheatlas://" + name

    exp_config_entity = AtlasEntity(
        name=name,
        typeName="custom_ml_exp_config",
        qualified_name=qn,
        guid = guid.get_guid(),
        attributes = config_attibutes
    )

    # Upload all entities!
    client.upload_entities(batch=[exp_config_entity.to_json()])
    
def create_model_entity(ws,experiment_name,modelname):
    # get deployed model
    from azureml.core.model import Model
    model = Model(ws, modelname)

    config_attibutes={}
    temp_column={}
    temp_column['workspace_name'] = model.workspace.name
    config_attibutes.update(temp_column)
    temp_column['workspace_subscription_id'] = model.workspace.subscription_id
    config_attibutes.update(temp_column)
    temp_column['workspace_subscription_id'] = model.workspace.subscription_id
    config_attibutes.update(temp_column)
    temp_column['workspace_resource_group'] = model.workspace.resource_group
    config_attibutes.update(temp_column)
    temp_column['name'] = model.name
    config_attibutes.update(temp_column)
    temp_column['id'] = model.id
    config_attibutes.update(temp_column)
    temp_column['version'] = model.version
    config_attibutes.update(temp_column)
    temp_column['tags'] = model.tags
    config_attibutes.update(temp_column)
    temp_column['properties'] = model.properties
    config_attibutes.update(temp_column)

    # Create a entity for Model
    name = modelname 
    qn = "pyapacheatlas://" + name

    exp_config_entity = AtlasEntity(
        name=name,
        typeName="custom_ml_model",
        qualified_name=qn,
        guid = guid.get_guid(),
        attributes = config_attibutes
    )

    # Upload all entities!
    client.upload_entities(batch=[exp_config_entity.to_json()])    
    
def create_model_metrics_entity(experiment_name,best_run):
    metrics = best_run.get_metrics()

    # select relevant metrics
    auc = metrics.get('AUC_weighted')
    accuracy = metrics.get('accuracy')
    precision = metrics.get('precision_score_weighted')
    recall = metrics.get('recall_score_weighted')
    f1 = metrics.get('f1_score_weighted')

    # # combine into single dataframe
    # metrics_df = sc.parallelize([['AUC', auc], ['Accuracy', accuracy], ['Precision', precision], ['Recall', recall], ['F1', f1]]).toDF(('Metric', 'Value'))
    metrics = ['AUC','Accuracy','Precision','Recall','F1']
    metricslist= [auc,accuracy,precision,recall,f1]
    columns = ['Metric','Value']
    metrics_df =  pd.DataFrame(zip(metrics, metricslist),columns=columns)


    dict_metrics = metrics_df.to_dict(orient = 'records')
    dict_metrics

    config_attibutes={}
    for attibutes in dict_metrics:
        temp_column={}
        temp_column[attibutes['Metric']] = attibutes['Value']
        config_attibutes.update(temp_column)
    config_attibutes

    name = experiment_name + "-modelmetrics"
    qn = "pyapacheatlas://" + name

    # Create a entity for model metrics
    exp_config_entity = AtlasEntity(
        name=name,
        typeName="custom_ml_model_metrics",
        qualified_name=qn,
        guid = guid.get_guid(),
        attributes = config_attibutes
    )

    # Upload all entities!
    client.upload_entities(batch=[exp_config_entity.to_json()])
    
def create_experiment_lineage(experimentname,exp_data_qn,exp_config_qn,model_metrics_qn,model_qn):        
    # create experiment process 
    # inputs: prepareddata, modelconfig 
    # outputs: model metrics and registered model

    from pyapacheatlas.core import AtlasProcess

    in_data_ent_guid = get_entity_guid(exp_data_qn,'custom_dataset')
    in_exp_config_guid = get_entity_guid(exp_config_qn,'custom_ml_exp_config')
    out_model_metrics_guid = get_entity_guid(model_metrics_qn,'custom_ml_model_metrics')
    out_model_guid = get_entity_guid(model_qn,'custom_ml_model')

    process_name = experimentname + '-train'
    process_qn = "pyapacheatlas://" + process_name
    process_type_name = "Process"

    process = AtlasProcess(
        name=process_name,
        typeName=process_type_name,
        qualified_name=process_qn,
        inputs = [{"guid":in_data_ent_guid},{"guid":in_exp_config_guid}],
        outputs = [{"guid":out_model_metrics_guid},{"guid":out_model_guid}],
        guid=guid.get_guid()
    )

    # Prepare all the entities as a batch to be uploaded.
    batch = [process]
    batch

    # Upload all entities!
    client.upload_entities(batch=batch)  
    
def create_model_service_entity(ws,experimentname,aci_service_name,samplejson):
    # get deployed ACI Web Service
    from azureml.core.webservice import AciWebservice
    aciws = AciWebservice(ws, aci_service_name)

    config_attibutes={}
    temp_column={}
    temp_column['workspace_name'] = aciws.workspace.name
    config_attibutes.update(temp_column)
    temp_column['workspace_subscription_id'] = aciws.workspace.subscription_id
    config_attibutes.update(temp_column)
    temp_column['workspace_resource_group'] = aciws.workspace.resource_group
    config_attibutes.update(temp_column)
    temp_column['name'] = aciws.name
    config_attibutes.update(temp_column)
    temp_column['image_id'] = aciws.image_id
    config_attibutes.update(temp_column)
    temp_column['compute_type'] = aciws.compute_type
    config_attibutes.update(temp_column)
    temp_column['state'] = aciws.state
    config_attibutes.update(temp_column)
    temp_column['scoring_uri'] = aciws.scoring_uri
    config_attibutes.update(temp_column)
    temp_column['tags'] = aciws.tags
    config_attibutes.update(temp_column)
    temp_column['state'] = aciws.state
    config_attibutes.update(temp_column)
    temp_column['properties'] = aciws.properties
    config_attibutes.update(temp_column)
    temp_column['created_by'] = aciws.created_by
    config_attibutes.update(temp_column)
    temp_column['sample_json'] = samplejson
    config_attibutes.update(temp_column)

    name = experimentname + "-model_endpoint"
    qn = "pyapacheatlas://" + name

    # Create a entity for ACI Web Service
    endpoint_entity = AtlasEntity(
        name=name,
        typeName="custom_ml_model_endpoint",
        qualified_name=qn,
        guid = guid.get_guid(),
        attributes = config_attibutes
    )

    # Upload all entities!
    client.upload_entities(batch=[endpoint_entity.to_json()])    
    
def create_powerbi_dataset_and_lineage(experiment_name,pbi_workspace,pbi_datasetid,pbidata_ent_name,ml_dataset_ent_name,ml_dataset_ent_type):
    
    pbidata_entity_type = 'powerbi_dataset'
    pbidata_ent_qn = pbi_workspace + '/datasets/' + pbi_datasetid 
    purview_basepath = 'pyapacheatlas://'
    #"https://msit.powerbi.com/groups/7d666287-f9b8-45ff-be6c-9909afe9df40/datasets/e5a30c22-466d-4a30-a1ac-8736ed6567cc"

    pbidata_ent = AtlasEntity(
        name=pbidata_ent_name,
        typeName=pbidata_entity_type,
        qualified_name= pbidata_ent_qn,
        workspace = pbi_workspace,
        guid = guid.get_guid()
    )

    # Prepare all the entities as a batch to be uploaded.
    batch = [pbidata_ent]
    batch

    # Upload all entities!
    client.upload_entities(batch=batch)

    #cretae powerbi_dataset_process lineage
    in_ent_guids = []
    in_ent_guid = get_entity_guid(purview_basepath + ml_dataset_ent_name,ml_dataset_ent_type)
    in_ent_guids.append({'guid':in_ent_guid})

    out_ent_guids = []
    out_ent_guid = get_entity_guid(pbidata_ent_qn,pbidata_entity_type)
    out_ent_guids.append({'guid':out_ent_guid})

    process_name =  'createpowerbidataset' + pbidata_ent_name + experiment_name
    process_qn = "pyapacheatlas://" + process_name
    process_type_name = "powerbi_dataset_process"

    process = AtlasProcess(
        name=process_name,
        typeName=process_type_name,
        qualified_name=process_qn,
        inputs = in_ent_guids,
        outputs = out_ent_guids,
        guid=guid.get_guid()
    )

    # Prepare all the entities as a batch to be uploaded.
    batch = [process]
    batch

    # Upload all entities!
    client.upload_entities(batch=batch)
    
def create_powerbi_report_and_lineage(experiment_name,pbi_workspace,pbi_reportid,pbi_ent_name,pbi_datasetid):

    #create powerbi report
    pbi_entity_type = 'powerbi_report'
    pbi_ent_qn = pbi_workspace + '/reports/' + pbi_reportid 
    purview_basepath = 'pyapacheatlas://'
    
    pbi_ent = AtlasEntity(
        name=pbi_ent_name,
        typeName=pbi_entity_type,
        qualified_name= pbi_ent_qn, 
        workspace = pbi_workspace,
        guid = guid.get_guid()
    )

    # Prepare all the entities as a batch to be uploaded.
    batch = [pbi_ent]
    batch

    # Upload all entities!
    client.upload_entities(batch=batch)

    #create powerbi dashboard process lineage
    pbidata_ent_qn = pbi_workspace + '/datasets/' + pbi_datasetid 
    in_ent_guids = []
    in_ent_guid = get_entity_guid(pbidata_ent_qn,'powerbi_dataset')
    in_ent_guids.append({'guid':in_ent_guid})

    out_ent_guids = []
    out_ent_guid = get_entity_guid(pbi_ent_qn,'powerbi_report')
    out_ent_guids.append({'guid':out_ent_guid})

    process_name = 'createpowerbireport' + pbi_ent_name + experiment_name
    process_qn = "pyapacheatlas://" + process_name
    process_type_name = "powerbi_report_process"

    process = AtlasProcess(
        name=process_name,
        typeName=process_type_name,
        qualified_name=process_qn,
        inputs = in_ent_guids,
        outputs = out_ent_guids,
        guid=guid.get_guid()
    )

    # Prepare all the entities as a batch to be uploaded.
    batch = [process]
    batch

    # Upload all entities!
    client.upload_entities(batch=batch)
    
# clean up datasets
def cleanup_entities(typename, entitytype):
    filter_setup = {"typeName": typename, "includeSubTypes": True}
    search = client.search_entities("*", search_filter=filter_setup)
    for entity in search:
        #print(entity)
        if entity.get("entityType") == entitytype:
            print(entity.get("id"),entity.get("qualifiedName"),entity.get("entityType"))
            guid = entity.get("id")
            client.delete_entity(guid=guid)

