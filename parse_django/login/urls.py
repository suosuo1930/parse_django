from django.urls import re_path, path
from login.luoji import foreground

urlpatterns = [
    re_path(r'one$', foreground.One.as_view(), name="one"),
    path('/two', foreground.Two, name='two'),


]