import ctypes
import win32.win32api as win32api

from .error import _capture_defined_win_error

from typing import Tuple


@_capture_defined_win_error('ChangeDisplaySettings')
def set_resolution(width=None, height=None, depth=32):
    '''Sets the primary windows display resolution.

    The resolution must be an existing preset. To reset to default resolution,
    pass in `None` for width and Height.
    '''

    if width is None and height is None:
        return win32api.ChangeDisplaySettings(None, 0)

    mode = win32api.EnumDisplaySettings()
    mode.PelsWidth = width
    mode.PelsHeight = height
    mode.BitsPerPel = depth

    return win32api.ChangeDisplaySettings(mode, 0)


def current_resolution() -> Tuple[int, int]:
    user32 = ctypes.windll.user32
    user32.SetProcessDPIAware()
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
