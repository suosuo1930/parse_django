import itertools
from itertools import count
from itertools import cycle,repeat
from itertools import accumulate

# ss = [e for e in dir(itertools) if not e.startswith('_')]
# for item in ss:
#     print(item)
#
# if __name__ == '__main__':
#     shi = count(10, 2)
#     i = 0
#     while i < 10:
#         print(shi.__next__())
#         i += 1
#         print("i==", i)

# one = cycle([100, 200, 300])
# if __name__ == '__main__':
#     i = 0
#     while i < 10:
#         print(next(one))
#         i += 1


# two = repeat([100, 200, 300], 100)
#
# for k, item in enumerate(two):
#     print(k, item)

def shi(val):
    return val + 10

ss = 0
three = accumulate(10,shi)
for k in shi:
    print(k)
    ss += 1
    if ss > 100:
        break





