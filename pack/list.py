# list

import os
import sys

# 获取当前文件所在目录的父目录（即项目根目录）
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # 项目根目录

# 将core目录添加到系统路径
core_dir = os.path.join(parent_dir, 'core')
sys.path.insert(0, core_dir)

from Parser import *

packall = {}

def pack_register(thing):
    global packall
    packall[thing.__name__] = thing

@pack_register
def push(nlist: EW_List, ins: EW_Type) -> EW_List:
    clog(f'Running list.push, nlist: {nlist}, ins: {ins}')
    return EW_List(nlist.value + [ins])
