from django.urls import path

from suosuo import views

urlpatterns = [
    path('view', views.viewDemo, name="view"),
    path('', views.index, name="index"),

]