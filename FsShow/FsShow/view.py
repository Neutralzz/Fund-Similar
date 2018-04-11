# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response, Http404, HttpResponseRedirect, render
from django.template import Context, RequestContext, loader
from django.http import HttpResponse
from django.http import JsonResponse
from django.utils import timezone

import os,sys,time
import json



def home(req):
    return render(req,"home.html",{"zscode":"sh000001,sz399001,sh000300,sz399006,sz399005,sh000016".split(',')})

def top(req):
    date = req.GET.get('date',None)
    return render(req,"toplist.html",{'date':date})

def search(req):
    code = req.GET.get('fundcode','000001')
    date = req.GET.get('date', None)    
    width = req.GET.get('len',None)
    if '-' not in date:
        date = None
    if 'code' == '':
        code = '000001'
    return render(req,"search.html",{'code':code,'date':date,'len':width,'timetick':int(time.time())})



