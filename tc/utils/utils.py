import inspect
import os.path


class Limit:
    ''' The limit object provides the ability to ask if a number is an
        a range. Upper and lower bound inclusive.

        Usage: create a limit with l = Limit(lower=10).
            >>> l = Limit(lower=10).
            >>> 5 in l == False
            >>> 50 in l == True
    '''

    def __init__(self, lower=0, upper=None):
        self.lower = lower
        self.upper = upper

    def __contains__(self, number):
        return ((self.lower is None or self.lower <= number) and
                (self.upper is None or self.upper >= number))


def __localfile(path: str) -> str:
    ''' Returns the path of a file relative to the source code file, instead
        of the working directory.
        ** NOTE: this means relative to THIS source file (utils.py), not where
                 you imported this function. **
    '''
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), path)


def __caller_filename() -> str:
    ''' Returns the file name of the caller function. This can be used to
        obtain the file name of a source code file calling this function,
        regardless of where the function was defined. '''
    return inspect.stack()[1].filename


def __trace(show_arguments=False, show_return=False):
    def trace(function):
        ''' Traces a function call by printing the function and its arguments
            before calling it, and printing the function and its return values
            after calling it.

            This function is a decorator function, and returns a function according
            to the above description.

            Usage:
            @trace
            def hello(name):
                return 'Hello, ' + name + '!'
            hello('John')
            >>> > hello :  'John'
                < Hello -> 'Hello, John!'
        '''
        def traced(*args, **kwargs):
            entry = '> ' + function.__name__
            if show_arguments:
                entry += ' :  ' + ', '.join(
                    [repr(arg) for arg in args] +
                    [key + '=' + repr(arg) for key, arg in kwargs.items()]
                )
            print(entry)
            result = function(*args, **kwargs)
            exit_ = '< ' + function.__name__
            if show_return:
                exit_ += ' -> ' + repr(result)
            print(exit_)
            return result
        return traced
    return trace


def trace(function):
    ''' Used as a decorator: traces function calls, arguments, and return values. '''
    return __trace(True, True)(function)


def simple_trace(function):
    ''' Used as a decorator: traces function calls, without seeing arguments and return values. '''
    return __trace()(function)


_default_encodings = ('utf-8', 'windows-1252', 'ascii', 'gb2312', 'gb18030',
                      'shift-jis', 'hz', 'big5')
def encoding_analysis(string: str, encodings=_default_encodings, show_errors=True):
    ''' Attempts to convert (wrongly encoded) text from one encoding to another,
        printing the results of all of the attempts. '''
    for src in encodings:
        for tgt in encodings:
            if src != tgt:
                if show_errors:
                    result = string.encode(src, errors='replace').decode(tgt, errors='replace')
                else:
                    try:
                        result = string.encode(src).decode(tgt)
                    except UnicodeError:
                        continue
                print(f'{src} -> {tgt}:\n\t{result}')
