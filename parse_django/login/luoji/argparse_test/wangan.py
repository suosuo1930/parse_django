
import argparse

parser = argparse.ArgumentParser(description="is first  argument parser",
                                 usage="fdfdfdfd", add_help=True ,)


parser.add_argument("-s", "--shiwei", help="shiwei is eat  cao")
#
# parser.add_argument("-w", "--wanganshi", help="wanganshi  is play basketball ", action="store_true")
#
#
# parser.add_argument("dd", type=int, help="delete argument")
#
# parser.add_argument("--ddfdf", type=int, choices=[1, 2, 3], help="dfjdfjkdf")
#
# parser.add_argument("-g", "--group", type=int, default=100, help="default  argument")

parser.add_argument("--reload", help="reload  config for chengxu", required=False, default=100, type=int)


ss, args = parser.parse_known_args()
print(" all >>", ss)
print("args all >>> ", args)

# print("shiwei>>>", ss.shiwei)
# print("wanganshi>>>", ss.wanganshi)
# print("delete>>>", ss.dd)
# print("default>>>", ss.group)
#
#
#
# if ss.shiwei:
#     print("ss.shiwei is  have  ")
# if ss.wanganshi:
#     print("ss.wanganshi is  True ")
# if ss.group:
#     print("deafault  ping fang:{}**2 = {}".format(ss.group, ss.group**2))

if ss.reload:
    print("reload is exists ==",  ss.reload)







