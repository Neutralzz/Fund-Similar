# -*- coding: utf-8 -*-
import sys,os,time

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import json
import pymongo
import config

from tornado.options import define, options
define("port", default=8088, help="run on the given port", type=int)


global mongo_cli
mongo_cli = pymongo.MongoClient('mongodb://%s:%s@127.0.0.1:27613' % (config.dbuser,config.dbpwd))

class DataHandler(tornado.web.RequestHandler):
    def get(self):
        global mongo_cli
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        callback = self.get_argument('callback','')
        code = self.get_argument('code')
        date = self.get_argument('date',time.strftime("%Y-%m-%d", time.localtime()))
        width = int(self.get_argument('len','20'))
        after = int(self.get_argument('after','0'))
        result = list(mongo_cli['fund-data'][code].find({'date':{'$lte':date}},{'date':1,'value':1,'name':1,'_id':0}).limit(width))
        result.reverse()
        if after != 0:
            after_res = list(mongo_cli['fund-data'][code].find({'date':{'$gt':date}},{'date':1,'value':1,'name':1,'_id':0}).sort('date',pymongo.ASCENDING).limit(after))
            while len(after_res) < after:
                after_res.append({'date':'-','value':'-','name':'-'})
            result = result + after_res
        #result = list(mongo_cli['fund-data'][code].find())[0]
        self.write(callback+'('+json.dumps(result)+')')
        self.finish()

class ResultHandler(tornado.web.RequestHandler):
    def get(self):
        global mongo_cli
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        callback = self.get_argument('callback','')
        code = self.get_argument('code')
        date = self.get_argument('date',None)
        width = int(self.get_argument('len','20'))
        result = []
        if date:
            result = list(mongo_cli['fund-similar'][code].find({'_id':date+','+str(width)}))
        else:
            result = list(mongo_cli['fund-similar'][code].find().sort('rdate',pymongo.DESCENDING).limit(1))
        self.write(callback+'('+json.dumps(result)+')')
        self.finish()

class InfoHandler(tornado.web.RequestHandler):
    def get(self,input):
        global mongo_cli
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        callback = self.get_argument('callback','')
        date = self.get_argument('date',time.strftime("%Y-%m-%d", time.localtime(time.time()-86400)))
        width = int(self.get_argument('len','20'))
        if input == 'top':
            result = list(mongo_cli['fund-info']['similar-top'].find({'_id':date+','+str(width)}))
            self.write(callback+'('+json.dumps(result)+')')
        self.finish()

def main():
    tornado.options.parse_command_line()
    app = tornado.web.Application(
        handlers=[
            (r"/jjjz/", DataHandler),
            (r"/xsjg/",ResultHandler),
            (r"/info/(\w+)",InfoHandler)
        ]
    )
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.bind(int(options.port), "0.0.0.0")# listen local only "127.0.0.1"
    http_server.start(1)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
