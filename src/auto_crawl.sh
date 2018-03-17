#!/bin/bash
Date=`date +%Y%m%d` &&
python3 crawl.py > ../log/crawl-"$Date".log 2>&1
