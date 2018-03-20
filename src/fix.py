# -*- coding: utf-8 -*-
from urllib import request
import sys,os,time,json
import pymongo
import config

global mongo_cli
mongo_cli = pymongo.MongoClient('mongodb://%s:%s@127.0.0.1:27613' % (config.dbuser,config.dbpwd))

codes = mongo_cli['fund-data'].collection_names(include_system_collections=False)

for code in codes:
    mongo_cli['fund-data'][code].create_index([('date',pymongo.DESCENDING)],unique=True)

