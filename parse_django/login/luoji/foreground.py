from django.core.signals import request_finished
from django.dispatch import Signal, receiver
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views import View

suosuo_signal = Signal()

# request_finished.connect(sender=)



class One(View):
    def get(self,request):
        suosuo_signal.send(sender=self.__class__,)
        return HttpResponse("SuoSuo is Good")

    def post(self, request):
        suosuo_signal.send_robust(sender=self.__class__)
        return JsonResponse({
            "code": 200,
            'msg': "is Successful",
        })

def Two(request):

    suosuo_signal.send_robust(sender=Two)
    return HttpResponse("is two func")
#
#
# @receiver(signal=[suosuo_signal,],)
# def basket(sender, **kwargs):
#     print('Signal %s, callback func: basket '%sender.__name__)
#     print('SuoSuo 的 信号接收器')

# def one():
#     print("one")
#
#
# def two():
#     print("two")
#
# def _three():
#     print("__three")
#
# __all__ = ["one", "two", "_three"]

