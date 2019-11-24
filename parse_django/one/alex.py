
import os
import sys
# sys.path.append(os.path.dirname(os.path.dirname()))
from importlib import import_module

from two.three.inner import Foo



if __name__ == '__main__':
    # print(sys.path)
    # Foo().get_age()
    # for k, v in sys.modules.items():
    #     print(k, '------', v)
    # print(sys.modules[__name__])
    # entry = "django/contrib/auth"
    # # module = import_module(entry)
    # module = entry.partition('.')
    # print(module)
    # paths = list(getattr(import_module("django.contrib.auth"), '__path__', []))
    # file_name = getattr(import_module('django.contrib.auth'), '__file__', '')
    # print(paths)
    # print(file_name)
    # print([os.path.dirname(file_name)])
    # os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')

    # shi = "wang"
    # wei = shi or "xijingping"
    # print(__path__)

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line()
    from django.apps import apps
    for k, v in apps.app_configs.items():
        print(k, '------', v)







