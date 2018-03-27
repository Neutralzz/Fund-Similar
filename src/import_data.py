#!/bin/python3
#coding=utf-8
import sys,os,time
import pymongo
from urllib import request
import config

global mongo_cli
mongo_cli = pymongo.MongoClient('mongodb://%s:%s@127.0.0.1:27613' % (config.dbuser,config.dbadmin))
	

def main():
    global mongo_cli    
    nowtime = int(1000*time.time())
    response = request.urlopen("http://fund.eastmoney.com/Data/Fund_JJJZ_Data.aspx?t=1&lx=3&letter=&gsid=&text=&sort=zdf,desc&page=1,9999&feature=|&dt=%d&atfc=&onlySale=0"%nowtime)
    html = response.read()
    content = str(html,encoding='utf-8')[7:]
    date,pdate = eval(content[content.find('showday:')+8:-1])
    print(date+' '+pdate)
    l = content.find('datas:') + 6
    r = content.find(',count')
    funddata = eval(content[l:r])
    
    for item in funddata:
        name = item[1]
        try:
            f = open('../data/'+item[0],'r')
            for line in f:
                row = line.split(',')
                dic = {
                    'code':item[0],
                    'name':item[1],
                    'update_time':  time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) ,
                    'value': float(row[1]),
                    'date' : row[0],
                    '_id' : item[0]+':'+row[0]
                }
                mongo_cli['fund-data'][item[0]].update({'_id':dic['_id']},{'$set':dic},upsert=True)
            f.close()
        except Exception as e:
            print(item[0]+' '+ repr(e))
        if item[3] == "":
            print(item[0]+' '+item[1]+' null')
            continue
        dic = {
            'code' : item[0],
            'name' : item[1],
            'update_time' : time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) ,
            'value' : float(item[3]),
            'date' : date,
            '_id' : item[0]+':'+date
        }
        mongo_cli['fund-data'][item[0]].update({'_id':dic['_id']},{'$set':dic},upsert=True)


if __name__ == '__main__':
    main()




