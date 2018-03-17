# -*- coding: utf-8 -*-
import os,sys

def getLastNLines(file, n):
    blk_size_max = 4096
    n_lines = []
    with open(file, 'r') as fp:
        fp.seek(0, os.SEEK_END)
        cur_pos = fp.tell()
        while cur_pos > 0 and len(n_lines) < n:
            blk_size = min(blk_size_max, cur_pos)
            fp.seek(cur_pos - blk_size, os.SEEK_SET)
            blk_data = fp.read(blk_size)
            lines = blk_data.split('\n')

            # adjust cur_pos
            if len(lines) > 1 and len(lines[0]) > 0:
                n_lines[0:0] = lines[1:]
                cur_pos -= (blk_size - len(lines[0]))
            else:
                n_lines[0:0] = lines
                cur_pos -= blk_size
            fp.seek(cur_pos, os.SEEK_SET)

    if len(n_lines) > 0 and len(n_lines[-1]) == 0:
        del n_lines[-1]
    return n_lines[-n:]
