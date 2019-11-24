

# s = [('Python', 1), ('Swift', 2), ('Python', 3), ('Swift', 4), ('Python', 9)]
# d = {}
# for k, v in s:
#     # setdefault()方法用于获取指定key对应的value.
#     # 如果该key不存在，则先将该key对应的value设置为默认值:[]
#     d.setdefault(k, []).append(v)
# print(list(d.items()))



# from collections import defaultdict
# s = [('Python', 1), ('Swift', 2), ('Python', 3), ('Swift', 4), ('Python', 9)]
# # 创建defaultdict，设置由list()函数来生成默认值
# d = defaultdict(list)
# for k, v in s:
#     # 直接访问defaultdict中指定key对应的value即可。
#     # 如果该key不存在，defaultdict会自动为该key生成默认值
#     d[k].append(v)
# print(list(d.items()))



# from collections import defaultdict
# my_dict = {}
#
# class Default:
#
#     def __str__(self):
#         return "defatlt"
#
#
# my_defaultdict = defaultdict(Default)
# print(my_defaultdict['a']) # 0
# print(my_dict['a']) # KeyError
import sys

# from hanqing import shiwei

from hanqing.shiwei import localss,lei, wang, wan

# print("--------", list(shiwei.__dict__.keys()))
# print("--------", list(sys.modules[shiwei.__name__].__dict__.keys()))

# import wei02



# print("main")
# localss()
# lei()
# wang()




