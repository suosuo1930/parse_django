# from collections import defaultdict
#
# def far():
#     print("sdf")
#     return "ss"
#
# ss = defaultdict(default_factory=far)
# ss.update(fdfd="dff", age = 200)
# di = [('Python', 1), ('Swift', 2), ('Python', 3), ('Swift', 4), ('Python', 9)]
# print(dict(di))
# print(ss)
# print(ss.get("name"))
import sys

print("global")

def localss():

    print("localss")

class lei:
    def __init__(self):
        print("lei init")

class wang:
    # __slots__ = ("__init__", "speak")

    __slots__ = '_local__impl', '__dict__'

    def __new__(cls, *args, **kwargs):
        print("wang  is new functions  ")
        return super().__new__(cls, *args, **kwargs)

    def __init__(self):
        print("-----------", hasattr(sys.modules[__name__], "wan"))
        print("wang init")
    def speak(self):
        print("is spesk")




#
# apps = lei()
wan = wang()
# print("---2222222222222222", hasattr(sys.modules[__name__], "wan"))
#
# print("++++++++++++++++, locals()==", list(locals().keys()))




