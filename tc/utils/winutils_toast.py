'''
This code is modified from github user jithurjacob's repo
    Windows-10-Toast-Notifications. The original license terms are reproduced below.


MIT License

Copyright (c) 2017 Jithu R Jacob

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''
from win32.win32gui import (
    CreateWindow, DestroyWindow, GetModuleHandle, PostQuitMessage, RegisterClass,
    Shell_NotifyIcon, UnregisterClass, UpdateWindow, NIF_INFO, NIF_MESSAGE,
    NIF_TIP, NIM_ADD, NIM_DELETE, NIM_MODIFY, WNDCLASS
)

from win32con import CW_USEDEFAULT, WM_DESTROY, WM_USER, WS_OVERLAPPED, WS_SYSMENU

class ToastNotifier(object):
    CLASS_NAME = 'PythonTaskbar'

    def __init__(self):
        # Register the window class.
        wc = WNDCLASS()
        wc.hInstance = GetModuleHandle(None)
        wc.lpszClassName = ToastNotifier.CLASS_NAME
        wc.lpfnWndProc = { WM_DESTROY: self.on_destroy }

        class_atom = RegisterClass(wc)

        style = WS_OVERLAPPED | WS_SYSMENU
        self.hwnd = CreateWindow(class_atom, ToastNotifier.CLASS_NAME, style,
            0, 0, CW_USEDEFAULT, CW_USEDEFAULT, 0, 0, wc.hInstance, None)

        UpdateWindow(self.hwnd)

        nif_flags = NIF_MESSAGE | NIF_TIP
        Shell_NotifyIcon(NIM_ADD, (self.hwnd, 0, nif_flags, WM_USER + 20, None, 'Python ToastNotifier Source'))

    def show_toast(self, title='Notification', message='example message', icon_path=None):
        Shell_NotifyIcon(NIM_MODIFY,
            (self.hwnd, 0, NIF_INFO, WM_USER + 20, None, '', message, 200, title))

    def on_destroy(self, hwnd, message, wparam, lparam):
        Shell_NotifyIcon(NIM_DELETE, (self.hwnd, 0))
        PostQuitMessage(0)

    def destroy(self):
        DestroyWindow(self.hwnd)
        UnregisterClass(ToastNotifier.CLASS_NAME, None)


if __name__ == "__main__":
    toaster = ToastNotifier()
    toaster.show_toast()
    toaster.destroy()
