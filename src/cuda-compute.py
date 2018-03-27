from numba import cuda,jit
import numpy as np
import math
import os,sys
import time
import config
import pymongo
import argparse

global mongo_cli, sMat, sMat_info, width, RESNUM
mongo_cli = pymongo.MongoClient('mongodb://%s:%s@47.94.128.239:27613' % (config.dbuser,config.dbpwd))


"""
width 是数据的宽度
len 是长序列长度
s_id 是短序列id
lMat.shape = (2,len+1)
sMat.shape = (s_num, width)
result.shape = (s_num, res_num, 3)
result是记录每个短序列结果的矩阵 0是相似度，1是对应长序列id，2是在长序列相似比较的开始日期

涨跌幅序列
lMat = [[l_id, a_0, a_1, a_2, ... , a_(len-1)],
        [l_id, b_0, b_1, b_2, ... , b_(len-1)]]
sMat = [
    [a_0, a_1, a_2, ... , a_(len-1)],    
    ...
]

"""
@cuda.jit
def compute(lMat,sMat,result):
    lm_len = lMat.shape[1]
    sm_num,width = sMat.shape
    res_bound = result.shape[1]
    # Thread id in a 1D block
    tx = cuda.threadIdx.x
    # Block id in a 1D grid
    ty = cuda.blockIdx.x
    # Block width, i.e. number of threads per block
    bw = cuda.blockDim.x
    # Compute flattened index inside the array
    pos = tx + ty * bw

    l_id = lMat[0][0]

    if pos < sm_num:
        for i in range(1, lm_len-width+1):
            ans = 0
            s1,s2 = 0,0
            for j in range(width):
                ans += lMat[0][i+j] * sMat[pos][j]
                s1 += lMat[0][i+j] * lMat[0][i+j]
                s2 += sMat[pos][j] * sMat[pos][j]
            if s1 < 1e-6:
                s1 = 1e-6
            if s2 < 1e-6:
                s2 = 1e-6
            ans = ans / math.sqrt(s1) / math.sqrt(s2)
            #if maxvalue[pos] < ans:
            #    maxvalue[pos] = ans
            j = res_bound - 1
            while j >= 0:
                if result[pos][j][0] + 1e-6 < ans:
                    if j+1 != res_bound:
                        result[pos][j+1][0] = result[pos][j][0]
                        result[pos][j+1][1] = result[pos][j][1]
                        result[pos][j+1][2] = result[pos][j][2]
                else:
                    break
                j -= 1
            if j+1 != res_bound:
                result[pos][j+1][0] = ans
                result[pos][j+1][1] = l_id
                result[pos][j+1][2] = lMat[1][i+width-1]


def load_data(cur_date):
    global sMat, sMat_info, mongo_cli, width
    codes = mongo_cli['fund-data'].collection_names(include_system_collections=False)
    sMat = []
    sMat_info = []

    #count = 0
    for code in codes:
        target = list(mongo_cli['fund-data'][code].find( { 'date' : {'$lte' : cur_date} } , {'date':1,'value':1}).\
                    sort('date',pymongo.DESCENDING).limit(width+1))
        target.reverse()
        if len(target) != width+1:
            continue

        print('load short seqence : %s'%code)

        sMat_info.append({
                'date' : target[-1]['date'],
                'code' : code
            })
        L = []
        for i in range(1,len(target)):
            if target[i-1]['value'] < 1e-4:
                target[i-1]['value'] = 1e-4
            L.append(1000*(target[i]['value']/target[i-1]['value']-1))
        sMat.append(L)

        #count+= 1
        #if count == 100:
        #    break
    sMat = np.array(sMat,np.float32)

def solve(cur_date):
    global mongo_cli, sMat, sMat_info, width, RESNUM

    time_prog_start = time.time()
    time_prog_compute = 0

    # load short seqences
    load_data(cur_date)
    print('load short seqences finish.')

    #time.sleep(10)

    threadsperblock = 64
    blockspergrid = int(math.ceil(sMat.shape[0] / threadsperblock))

    # load each long seqence
    codes = mongo_cli['fund-data'].collection_names(include_system_collections=False)
    
    result = np.zeros((sMat.shape[0], RESNUM, 3), dtype=np.float32)
    #maxvalue = np.zeros((sMat.shape[0]),dtype=np.float32)

    for code in codes:
        
        time_start = time.time()
        
        target = list(mongo_cli['fund-data'][code].find( { 'date' : {'$lte' : cur_date} } , {'date':1,'value':1}))
        
        # not enough long
        if len(target) < width + width/2 + 1:
            continue

        l_id = int(code) + 1e6
        L1,L2 = [l_id],[l_id]

        for i in range(1,len(target)-int(width/2)):
            if target[i-1]['value'] < 1e-4:
                target[i-1]['value'] = 1e-4
            L1.append(1000*(target[i]['value']/target[i-1]['value']-1))
            L2.append(time.mktime(time.strptime(target[i]['date'],'%Y-%m-%d')))

        lMat = [L1,L2]
        lMat = np.array(lMat, np.float32)

        time_compute = time.time()
        compute[blockspergrid,threadsperblock](lMat, sMat, result)
        time_prog_compute += float(time.time() - time_compute)
        #print("current max value : %.4f"%(float(maxvalue[np.argmax(maxvalue)])))
        print("%s : compute time %.4f , all time %.4f"%(code,float(time.time() - time_compute),float(time.time() - time_start)))
        #break
    """
    for i in range(len(sMat_info)):
        code = sMat_info[i]['code']
        dic = {}
        dic['_id'] = sMat_info[i]['date']+','+str(width)
        dic['rdate'] = sMat_info[i]['date']
        dic['update_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        dic['similar'] = []
        for j in range(1):
            dic['similar'].append({
                'code': str(int(result[i][j][1]))[1:],
                'rdate': time.strftime('%Y-%m-%d', time.localtime(result[i][j][2])),
                'similarity' : float(result[i][j][0])
                })
        print(dic)
    """
    for i in range(len(sMat_info)):
        code = sMat_info[i]['code']
        dic = {}
        dic['_id'] = sMat_info[i]['date']+','+str(width)
        dic['rdate'] = sMat_info[i]['date']
        dic['update_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        dic['similar'] = []
        for j in range(RESNUM):
            dic['similar'].append({
                'code': str(int(result[i][j][1]))[1:],
                'rdate': time.strftime('%Y-%m-%d', time.localtime(result[i][j][2])),
                'similarity' : float(result[i][j][0])
                })
        mongo_cli['fund-similar'][code].update({'_id':dic['_id']},{'$set':dic},upsert=True)

    print("total compute time %.4f , total used time %.4f."%(time_prog_compute,float(time.time()-time_prog_start)))

def main():
    global width,RESNUM
    parser = argparse.ArgumentParser(description='manual to this script')
    parser.add_argument('--date', type=str, default = time.strftime("%Y-%m-%d", time.localtime()))
    parser.add_argument('--width', type=int, default = 20)
    parser.add_argument('--resnum', type=int, default = 10)
    args = parser.parse_args()

    cur_date = args.date
    width = args.width
    RESNUM = args.resnum
    solve(cur_date)

if __name__ == '__main__':
    main()