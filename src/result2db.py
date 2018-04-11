import pymongo
import json
import config

import os,sys
global mongo_cli
mongo_cli = pymongo.MongoClient('mongodb://%s:%s@47.94.128.239:27613' % (config.dbuser,config.dbpwd))

def main():
	global mongo_cli
	for filename in os.listdir('../result'):
		file = open('../result/'+filename,'r')
		data = None
		for line in file:
			data = json.loads(line)
			break
		file.close()
		if len(filename) == 6:
			mongo_cli['fund-similar'][filename].update({'_id':data['_id']},{'$set':data},upsert=True)
		else:
			mongo_cli['fund-info']['similar-top'].update({'_id':data['_id']},{'$set':data},upsert=True)

if __name__ == '__main__':
	main()