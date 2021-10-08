import os
import json
from pymongo import MongoClient


def get_mongodb_config_info():
    with open(os.environ.get('TOOLKIT_CONFIG_NAME'), 'r') as rf:
        config = json.load(rf)
        return config['mongodb_host'], config['mongodb_port'], config['database']

def set_up_db_for_test(docs):
    db_host, db_port, db_name = get_mongodb_config_info()
    client = MongoClient(db_host, db_port)
    db_obj = client[db_name]
    coll = db_obj.assays
    for doc in docs:
        coll.insert_one(doc)

def teardown_db_for_test():
    db_host, db_port, db_name = get_mongodb_config_info()
    client = MongoClient(db_host, db_port)
    coll = client[db_name].assays
    old_versions_coll = client[db_name].assays_old_versions
    remove_resp = coll.delete_many({})
    resmove_oldversions_resp = old_versions_coll.delete_many({})

def query_for_all_docs():
    db_host, db_port, db_name = get_mongodb_config_info()
    client = MongoClient(db_host, db_port)
    coll = client[db_name].assays
    all_docs = list(coll.find({}))
    return all_docs

