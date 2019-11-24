import functools

# ss = [e for e in dir(functools) if not e.startswith('_')]
# for itme in ss:
#     print(itme)
#
#
# from functools import cmp_to_key
# class User:
#     def __init__(self, name):
#         self.name = name
#     def __repr__(self):
#         return 'User[name=%s' % self.name
# # 定义一个老式的大小比较函数，User的name越长，该User越大
# def old_cmp(u1 , u2):
#     return len(u1.name) - len(u2.name)
# my_data = [User('Kotlin'), User('Swift'), User('Go'), User('Java')]
# # 对my_data排序，需要关键字参数（调用cmp_to_key将old_cmp转换为关键字参数
# my_data.sort(key=cmp_to_key(old_cmp))
# print(my_data)


# from functools import partial
# # print(int('12345'))
# # # 为int函数的base参数指定参数值
# # basetwo = partial(int, base=2)
# # basetwo.__doc__ = '将二进制的字符串转换成整数'
# # # 相当于执行base为2的int()函数
# # print(basetwo('10010'))
# # print(int('10010', 2))




# @functools.lru_cache(maxsize=32)
# def factorial(n):
#     print('~~计算%d的阶乘~~' % n)
#     if n == 1:
#         return 1
#     else:
#         return n * factorial(n - 1)
# # 只有这行会计算，然后会缓存5、4、3、2、1的解乘
# print(factorial(5))
# print(factorial(3))
# print(factorial(5))







# @functools.total_ordering
# class User:
#     def __init__(self, name):
#         self.name = name
#     def __repr__(self):
#         return 'User[name=%s' % self.name
#     # 根据是否有name属性来决定是否可比较
#     def _is_valid_operand(self, other):
#         return hasattr(other, "name")
#     def __eq__(self, other):
#         if not self._is_valid_operand(other):
#             return NotImplemented
#         # 根据name判断是否相等（都转成小写比较、忽略大小写）
#         return self.name.lower()  == other.lastname.lower()
#     def __lt__(self, other):
#         if not self._is_valid_operand(other):
#             return NotImplemented
#         # 根据name判断是否相等（都转成小写比较、忽略大小写）
#         return self.lastname.lower() < other.lastname.lower()
# # 打印被装饰之后的User类中的__gt__方法
# print(User.__gt__)




# from functools import *
# @singledispatch
# def test(arg, verbose):
#     if verbose:
#         print("默认参数为：", end=" ")
#     print(arg)
# # 限制test函数第一个参数为int型的函数版本
# @test.register(int)
# def _(argu, verbose):
#     if verbose:
#         print("整型参数为：", end=" ")
#     print(argu)
# test('Python', True)  # ①
# # 调用第一个参数为int型的版本
# test(20, True)  # ②




from functools import wraps
def fk_decorator(f):
    # 让wrapper函数看上去就像f函数
    @wraps(f)
    def wrapper(*args, **kwds):
        """dfdf"""
        print('调用被装饰函数')
        return f(*args, **kwds)
    return wrapper
@fk_decorator
def test():
    """test函数的说明信息"""
    print('执行test函数')
test()
print(test.__name__)
print(test.__doc__)