import os

from django.core import serializers
from django.db.models import QuerySet
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from resi.models import Book
from suosuo.forms import BookForms, BookModleForm
import inspect

"""
'bound_data', 'clean', 'default_error_messages', 'default_validators', 'disabled',
 'empty_value', 'empty_values', 'error_messages', 'get_bound_field', 'has_changed', 
 'help_text', 'hidden_widget', 'initial', 'label', 'label_suffix', 'localize', 
 'max_length', 'min_length', 'prepare_value', 'required', 'run_validators', 
 'show_hidden_initial', 'strip', 'to_python', 'validate', 'validators', 
 'widget', 'widget_attrs'
"""

def index(request):
    form = BookModleForm()
    # print('form attrs ==', dir(form))
    # print('fields==', dir(form.fields.get("authors")))
    # for item in dir(form.fields.get("authors")):
    #     if not item.startswith("__"):
    #         data = getattr(form.fields.get("authors"),item)
    #         if inspect.isfunction(item):
    #             print(item ,"==func==", data())
    #         else:
    #             print(item ,"====", data)

    if request.method == "POST":
        form = BookModleForm(request.POST)
        print(form.data)
        if form.is_valid():
            print('clean_date=', form.cleaned_data)
            seria_data = serializers.serialize('json', Book.objects.all())
            print('序列化=', seria_data)
            return render(request, 'index.html', locals())


    return render(request, 'index.html', locals())


def viewDemo(request):
    form = BookModleForm()
    if request.method == "POST":
        form = BookModleForm(request.POST)
        if form.is_valid():
            book_obj = Book.objects.create(**form.cleaned_data)
            book_obj = QuerySet(book_obj)
            print("is right=", serializers.serialize('json', book_obj))
            return JsonResponse(serializers.serialize('json', book_obj))
    return render(request, 'viewDemo.html', locals())
