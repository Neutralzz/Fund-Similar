# -*- coding: utf-8 -*-
from urllib import request
import sys,os,time,json
import pymongo
import config

global mongo_cli
mongo_cli = pymongo.MongoClient('mongodb://%s:%s@127.0.0.1:27613' % (config.dbuser,config.dbpwd))

codes = mongo_cli['fund-similar'].collection_names(include_system_collections=False)


for day in ['19','20','21','22','23','26']:
    date = '2018-03-'+day
    simi_res = []
    for code in codes:
        L = list(mongo_cli['fund-similar'][code].find({'rdate':date}))
        if len(L) == 0:
            continue
        res = L[0]
        simi_res.append({
            'code_a' : code,
            'rdate_a' : date,
            'code_b' : res['similar'][0]['code'],
            'rdate_b' : res['similar'][0]['rdate'],
            'similarity' : res['similar'][0]['similarity']
        })
    simi_res = sorted(simi_res,key= lambda x : x['similarity'],reverse=True)
    simi_res = simi_res[0:200]
    simi_top = {
        '_id' : date+',20',
        'date' : date,
        'top' : simi_res
    }
    mongo_cli['fund-info']['similar-top'].update({'_id':simi_top['_id']},{'$set':simi_top},upsert=True)
        



        


