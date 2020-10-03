import os
import re
import typing.re
import tc.subfiles
import fnmatch
import sys
from natsort import natsorted
from send2trash import send2trash

from typing import List, Any, Iterable


def filesize_format(s: float, readable=True) -> Any:
    ''' converts a file size, s, in bytes, to a human-readable string '''
    if not readable:
        return s
    for suffix in 'B', 'KB', 'MB', 'GB', 'TB', 'PB':
        if s < 1024:
            return f'{s:.3g} {suffix}'
        s /= 1024
    return f'{s:.3g} EB'  # We assume we won't see this...


def filesize(file_or_dir: str, recursive=False, diskspace=False, return_data=None) -> int:
    ''' returns the size of a file, or directory, in bytes.
        if file_or_dir is a directory, recursive must be True.
        if file_or_dir is not a directory, recursive must be False.

        note: return_data kept for backwards compatibility but deprecated'''
    if return_data is not None:
        import warnings
        warnings.warn('argument return_data deprecated (tc.utils.fileutils.filesize)', DeprecationWarning)


    if diskspace:
        raise ValueError('disk space mode not yet implemented!')

    isdir = os.path.isdir(file_or_dir)

    if not isdir:
        if recursive:
            raise ValueError(f'{file_or_dir} is a file; do not specify recursive=True')
        stat = os.stat(file_or_dir, follow_symlinks=False)
        return stat.st_size

    # isdir
    if not recursive:
        raise ValueError(f'{file_or_dir} is a directory; specify recursive=True to traverse this directory')

    total = 0

    for f in tc.subfiles.get_elements(file_or_dir, filter=os.path.isfile):
        stat = os.stat(file_or_dir, follow_symlinks=False)
        total += stat.st_size
    return total


def print_filesize(file_or_dir: str, recursive=False, verbose=False,
                   levels=0, diskspace=False, readable=True):
    ''' Returns or prints the size of a file or directory.
        This implementation is incomplete
        *recursive* must be specified for a directory
        *verbose* lists every file before the summary
        *levels* specify how many levels for the summary
        *diskspace* counts space on disk instead of actual file size
            this argument does not do anything yet
        *readable* reports human readable file sizes instead of bytes '''
    try:
        fs = filesize(file_or_dir, recursive, diskspace)
    except Exception as e:
        print(str(e))
        return

    if not recursive:
        print(f'{filesize_format(fs)}\t{file_or_dir}')
        return

    # Recursive scanning not yet implemented
    if verbose:
        print('\nSUMMARY')

    raise NotImplementedError('Recursive Scanning not yet implemented!')


def find(root=os.path.curdir, pattern=None, mode='fnmatch', use_full_name=False) -> Iterable[str]:
    ''' Generates the full (relative) names off all files in a directory
        matching a pattern. '''

    if pattern is None or pattern == '':
        search_function = lambda _: True
    if type(pattern) is str and (mode is None or mode == ''):
        search_function = lambda p: p in pattern
    elif type(pattern) is str and mode == 'fnmatch':
        regex = re.compile(fnmatch.translate(pattern))
        search_function = lambda p: regex.search(p) is not None
    elif type(pattern) is str and mode == 'regex':
        regex = re.compile(pattern)
        search_function = lambda p: regex.search(p) is not None
    elif isinstance(pattern, typing.re.Pattern):
        search_function = lambda p: pattern.search(p) is not None
    else:
        raise ValueError('Invalid pattern and mode combination')

    if not os.path.isdir(root) and search_function(root):
        yield root

    for e in tc.subfiles.get_elements(root):
        if search_function(e if use_full_name else os.path.basename(e)):
            yield e


def is_hidden(file: str) -> bool:
    return os.path.basename(file).startswith('.')


def surface_trace(pathname: str, ignore_hidden=False) -> str:
    import warnings
    warnings.warn("this function has been renamed, and its old name deprecated: use 'traverse_to_contents' instead (tc.utils.fileutils.surface_trace)", DeprecationWarning)
    return traverse_to_contents(pathname, ignore_hidden)


def traverse_to_contents(pathname: str, ignore_hidden=False) -> str:
    ''' given a folder, recursively finds the deepest single-level folder.
        i.e. if pathname contains only one folder, returns
        traverse_to_contents(subfolder) otherwise returns pathname '''
    files = os.listdir(pathname)

    if ignore_hidden:
        files = [f for f in files if not is_hidden(f)]

    if len(files) == 1 and os.path.isdir(os.path.join(pathname, files[0])):
        return traverse_to_contents(os.path.join(pathname, files[0]))
    else:
        return pathname


def surface(path: str, naming='top', format_string='[{top}] {bottom}'):
    ''' 'Surfaces' a folder by traversing down it, and replacing its
        contents with the contents of the first folder that does not
        only contain a folder. '''
    bottom_path = traverse_to_contents(path)

    if path == bottom_path:
        print(f'folder {path} does not need surfacing', file=sys.stderr)
        return

    temp_name = path + '~temp'
    if naming == 'top':
        new_name = path
    elif naming == 'bottom':
        new_name = os.path.join(os.path.dirname(path), os.path.basename(bottom_path))
    elif naming == 'both':
        formatted = format_string.format(
            top=os.path.basename(path),
            bottom=os.path.basename(bottom_path)
        )
        new_name = os.path.join(os.path.dirname(path), formatted)
    else:
        print('error: name must be top, bottom, or both')
        return None

    os.rename(bottom_path, temp_name)
    send2trash(path)  # We can safely call os.remove here but I'm just to paranoid
    os.rename(temp_name, new_name)
    print(f'surfaced {bottom_path} -> {new_name}', file=sys.stderr)


def explode(folder: str):
    ''' 'explodes' a folder my moving all its contents to its parent directory,
        and then deleting it. '''
    if not os.path.isdir(folder):
        raise ValueError(f'{folder} is not a valid directory')

    folder = os.path.abspath(folder)

    files = os.listdir(folder)
    parent, _ = os.path.split(folder)

    for filename in os.listdir(folder):
        original_name = os.path.join(folder, filename)
        move(original_name, folder=parent)

    os.rmdir(folder)


def alternative_filename(
    filename: str,
    testfunc=os.path.exists,
    error_on_good_input=False,
    format_string='{basename} ({counter})',
    counter_begin=1
) -> str:
    ''' Returns an available file name, given a proposed file name.

    By default, mimics Windows file renaming rules.

    Optionally, raises an error when the input file name is already available
    '''
    if not testfunc(filename):
        if error_on_good_input:
            raise ValueError(f"'{filename}' does not need an alternative name")
        return filename

    alt_count = counter_begin
    basename, ext = os.path.splitext(filename)
    while True:
        target_filename = format_string.format(basename=basename, counter=alt_count) + ext
        if not testfunc(target_filename):
            return target_filename
        alt_count += 1


def move(
    file_or_folder: str, *,
    folder: str = None,
    name: str = None,
    filename: str = None,  # equivalent to `name`, kept for compatibility reasons
    auto_rename=True,
    makedirs=False,
) -> str:
    '''Moves a file or folder.

    At least one of `name` and `folder` must be provided

    If only `folder` is provided, the file or folder is moved to the provided folder.

    If only `name` is provided, similar to calling `os.rename`

    If both `folder` and `name` is provided, the file is renamed to `name` and moved
    the the provided folder. `name` must not contain path separators in this case.

    Returns the real name of the moved file.
    '''

    # for backwards compatibility
    if name is None and filename is not None:
        name = filename

    if folder is None:
        if name is None:
            raise ValueError('one of folder or filename must be provided')
        if os.path.isabs(name):
            target_name = name
        else:
            target_name = os.path.join(os.path.curdir, name)
    else:
        if name is None:
            target_name = os.path.join(folder, os.path.basename(file_or_folder))
        else:
            if os.path.dirname(name) != '':
                raise ValueError('name cannot contain path separators when folder is provided')
            target_name = os.path.join(folder, name)

    # don't rename something to itself
    if os.path.normpath(os.path.normcase(file_or_folder)) == os.path.normpath(os.path.normcase(target_name)):
        return file_or_folder

    target_name = alternative_filename(target_name)

    if makedirs and not os.path.exists(os.path.dirname(target_name)):
        os.makedirs(os.path.dirname(target_name))

    os.rename(file_or_folder, target_name)
    print(f'moved {file_or_folder} -> {target_name}', file=sys.stderr)
    return target_name


def rename(file_or_folder: str, name: str, *, auto_rename=True) -> str:
    '''Renames a file or folder.

    The file or folder is kept in its original folder, and it's name is changed.

    Returns the resulting name of the moved file.
    '''

    if os.path.dirname(name) != '':
        raise ValueError('name cannot contain path separators')

    return move(file_or_folder,
                folder=os.path.dirname(file_or_folder),
                name=name,
                auto_rename=auto_rename)


def order(folder=os.path.curdir, start=0, filter=None, mode='replace', format_string=None):
    contents = natsorted(os.listdir(folder))

    rename_queue = []

    current = start
    for f in contents:
        if filter is not None and not filter(f):
            continue

        name, ext = os.path.splitext(f)
        if mode == 'replace':
            new_name = f'{current}{ext}'
        elif mode == 'front':
            new_name = f'{name} {current}{ext}'
        elif mode == 'format':
            new_name = format_string.format(i=current, name=name) + ext
        else:
            print('error: mode must be replace, front or format', file=sys.stderr)
            return

        temp_name = move(os.path.join(folder, f), folder=folder, filename=new_name)
        if os.path.basename(temp_name) != new_name:
            rename_queue.append([temp_name, new_name])

        current += 1

    for source, target in rename_queue:
        final_name = move(source, folder=folder, filename=target)
        if os.path.basename(target) != target:
            print('warning: final name does not match predicted name!', file=sys.stderr)


def listdir(path=os.path.curdir) -> List[str]:
    return natsorted(os.listdir(path))


_default_preprocess = {
    '*': ' ',
    '"': '\'',
    '/:': '-'
}

def sanitize_filename(
    filename: str, target='windows', replace_with='_', preprocess=_default_preprocess
) -> str:
    _win_fn_max = 200  # note: it's actually 255, but sometimes it's buggy
    if target.lower() != 'windows':
        raise ValueError('non-windows platforms not yet supported!')

    for key, value in preprocess.items():
        for character in key:
            filename = filename.replace(character, value)

    sanitized = re.sub(r'[\\/:*?\"<>|]', '_', filename)
    if len(filename) > _win_fn_max:
        base, ext = os.path.splitext(sanitized)
        base = base[:_win_fn_max-(len(ext)+3)] + '...'
        sanitized = base + ext

    return sanitized


def reencode(file: str, source='cp932', dest='utf-8'):
    with open(file, encoding=dest) as infile:
        try:
            infile.read()
            print('File already in ' + dest + ' encoding', file=sys.stderr)
            return
        except UnicodeDecodeError:
            pass
    with open(file, encoding=source) as infile:
        try:
            contents = infile.read()
        except UnicodeDecodeError:
            print('File could not be read as ' + source)
            return
    os.rename(file, file + '.backup')
    with open(file, 'w', encoding=dest) as outfile:
        outfile.write(contents)


common_image_extensions = frozenset((
    '.png', '.bmp', '.gif', '.heic', '.heif', '.j2k', '.jfi', '.jfif', '.jif',
    '.jp2', '.jpe', '.jpeg', '.jpf', '.jpg', '.jpm', '.jpx', '.mj2', '.tif',
    '.tiff', '.webp'
))

uncommon_image_extensions = frozenset((
    '.ari', '.ani', '.arw', '.bay', '.bpg' '.3fr', '.cap', '.cr2' '.cr3',
    '.crw', '.data', '.dcr', '.dcs', '.dib', '.dng', '.drf', '.eip', '.erf',
    '.fff', '.flif', '.gpr', '.hdr', '.iiq', '.jng', '.k25', '.kdc', '.mdc',
    '.mef', '.mos', '.mrw', '.nef', '.nrw', '.obm', '.orf', '.pbm', '.pef',
    '.pgm', '.pnm', '.ppm', '.ptx', '.pxn', '.r3d', '.raf', '.raw', '.rw2',
    '.rwl', '.rwz', '.sr2', '.srf', '.srw', '.x3f'
))

def is_common_image(filename: str) -> bool:
    _, ext = os.path.splitext(filename)
    return ext in common_image_extensions


def is_image(filename: str) -> bool:
    _, ext = os.path.splitext(filename)
    return ext in common_image_extensions or ext in uncommon_image_extensions
