import sys
import warnings

from typing import Dict, Optional, Tuple, Literal, NamedTuple


class WinErrorSpecification(NamedTuple):
    type: Literal['success', 'warning', 'info', 'error']
    name: str
    message: Optional[str] = None


class WinError(Exception):
    def __init__(self, name: str, message=None):
        self.name = name
        self.message = message

    def __str__(self):
        if self.message is None:
            return f'{self.name}'

        return f'{self.message} ({self.name})'


class WinWarning(Warning):
    def __init__(self, name: str, message=None):
        self.name = name
        self.message = message

    def __str__(self):
        if self.message is None:
            return f'{self.name}'

        return f'{self.message} ({self.name})'


__win_errorcodes = {
    'ChangeDisplaySettings': {
        0: WinErrorSpecification(
            'success',
            'DISP_CHANGE_SUCCESSFUL',
            'The display settings were successfully changed.'),
        1: WinErrorSpecification(
            'info',
            'DISP_CHANGE_RESTART',
            'The computer must be restarted for the display changes to take effect.'),
        -1: WinErrorSpecification(
            'error',
            'DISP_CHANGE_FAILED',
            'The display driver failed the specified graphics mode.'),
        -2: WinErrorSpecification(
            'error',
            'DISP_CHANGE_BADMODE',
            'The specified graphics mode is not supported.'),
        -4: WinErrorSpecification(
            'error',
            'DISP_CHANGE_BADFLAGS',
            'An invalid set of flags was specified.'),
        -5: WinErrorSpecification(
            'error',
            'DISP_CHANGE_BADPARAM',
            'An invalid parameter was specified.')
    }
}


def _raise_win_error(value, errors: Dict[int, WinErrorSpecification]):
    if value in errors:
        error = errors[value]
        if error.type == 'success':
            return
        if error.type == 'info':
            print(error.message, file=sys.stderr)
            return
        if error.type == 'warning':
            warnings.warn(WinWarning(error.name, error.message))
            return
        if error.type == 'error':
            raise WinError(error.name, error.message)

    return value


def _capture_win_error(errors: Dict[int, WinErrorSpecification]):
    def capture_function(function):
        def captured_function(*args, **kwargs):
            return _raise_win_error(function(*args, **kwargs), errors)
        return captured_function
    return capture_function


def _capture_defined_win_error(name: str):
    return _capture_win_error(__win_errorcodes[name])
