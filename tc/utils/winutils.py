from typing import Callable, Type

import win32.win32api as wapi

from tc.utils.winutils_toast import ToastNotifier


def prompt_errors(*errors: Type[Exception]) -> Callable:
    ''' Prompts specified errors using a Windows MessageBox when calling a function.

        Usage:
        >>> @prompt_errors(KeyError)
            def could_error:
                ...
    '''
    def function_transformer(function: Callable) -> Callable:
        def with_error_prompts(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except errors as e:
                wapi.MessageBox(0, f'{e.__class__.__name__}: {e}', 'Error')
        return with_error_prompts
    return function_transformer


def toast_notification(title: str, message: str = ''):
    if message == '':
        title, message = message, title

    notifier = ToastNotifier()
    notifier.show_toast(title=title, message=message)
    notifier.destroy()
