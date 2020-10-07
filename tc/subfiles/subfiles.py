""" This file defines the subfiles_get class and its extensions, which
    provide iteration functionality subfiles and subfolders """
import os
from typing import Callable, Generic, Iterable, Iterator, List, Optional, Tuple, TypeVar, Union

from tc.utils import Limit

# note: the complicated typing structure is for mypy. as the programmer, is doesn't really give us any information.
T = TypeVar('T')
WalkNode = Tuple[str, List[str], List[str]]

class subfiles_get(Generic[T], Iterable[T]):
    """ Root class for get_x.
        Provides the ability to iterate through items acquired through
        calling os.walk.

        Only intended to be subclassed.

        Arguments:

        `depth`: a `range`-like object; only returns files in range;
                 depth=0 is equivalent to listdir;
                 can only traverse into depths <= 255
                 (developer's note: this is an arbitrary number)

        `limit`: an `int`; the maximum number of files to walk

        `filter`: `(str) -> bool`; results that return `False` are skipped

        `sort`: `(Iterable) -> Iterable`; used to sort files in a directory

        `topdown`: passed into `os.walk`
    """
    root: str
    limit: int
    walk: Iterable[WalkNode]
    filter_func: Optional[Callable[..., bool]]

    def __init__(self, root: str = os.path.curdir,
                 depth: Union[int, Tuple[int, int], Limit, range] = Limit(),
                 limit=None, filter=None, sort=None, topdown=True):
        self.root = os.path.abspath(root)

        if type(depth) == int:
            depth_range = range(depth + 1)
        elif type(depth) == tuple:
            if len(depth) >= 2:
                l, r, *s = depth
                depth_range = range(l, r + 1, *s)
            else:
                depth_range = range(*depth)
        else:
            depth_range = depth

        # used to optimize os.walk when topdown=True
        ignore_deeper_than = None
        for i in range(256):
            if i in depth_range:
                ignore_deeper_than = None
            elif ignore_deeper_than is None and i not in depth_range:
                ignore_deeper_than = i

        self.limit = limit

        if sort is None:
            sort_func = lambda x: x
        else:
            assert sort(['.']) == ['.']
            sort_func = sort

        def walk():
            for dirpath, dirnames, filenames in os.walk(root, topdown=topdown):
                depth = relative_depth(dirpath, self.root)
                if depth in depth_range:
                    yield dirpath, sort_func(dirnames), sort_func(filenames)

                if topdown and ignore_deeper_than is not None and depth + 1 >= ignore_deeper_than:
                    # empty the list in-place; see documentation for os.walk for more information
                    dirnames[:] = []


        self.walk = walk()

        self.filter_func = filter

    def __iter__(self) -> Iterator[T]:
        """ Iterates through "valid" items given by self.elements,
            filtered by self.filter,
            and returns "results" determined by self.process
        """
        for element in self.elements():
            if self.filter(element):
                if self.limit is not None:
                    if self.limit > 0:
                        self.limit -= 1
                    else:
                        return
                yield self.process(element)

    def elements(self) -> Iterable[T]:
        """ A generator function that iterates through possible return
            values based on the self.walk generator.
        """
        pass

    def process(self, element: T) -> T:
        """ Processes a retrieved element before yielding it, intended
            for use in a map function.
        """
        return element

    def filter(self, element: T) -> bool:
        """ Returns whether element is a valid element. Only valid
            elements are processed, yielded, and counted towards the
            limit.
        """
        if self.filter_func:
            return self.filter_func(element)

        return True


class subfiles_map(Generic[T], subfiles_get[T]):
    """ A class extension providing mapping ability to get_x classes.
        Works basically like python's map.

        Only intended to be subclassed.
    """
    def __init__(self, root: str = os.path.curdir, func=None, **kwargs):
        if func is None:
            raise TypeError('expected function, got None')
        super().__init__(root=root, **kwargs)
        self.func = func

    def execute(self):
        """ Iterates through the subfiles_map object, executes the input
            function, and discards the result.
        """
        for _ in self:
            pass

    def process(self, element: T):
        return self.func(element)


def relative_depth(path: str, root=os.path.curdir) -> int:
    """ Returns the relative depth of a path. i.e. number of folders
        forward minus number of folders backwards.
    """
    if not path:
        return 0

    previous_paths, current_path = os.path.split(os.path.relpath(path, root))

    if current_path == root:
        return 0
    else:
        if current_path == os.path.pardir:
            path_modifier = -1
        elif current_path == os.path.curdir:
            path_modifier = 0
        else:
            path_modifier = 1
        return relative_depth(previous_paths) + path_modifier


class get_dirs(subfiles_get[WalkNode]):
    """ get_dirs(root=os.path.curdir,
        depth=contains_all(), limit=None, filter=None)
        --> subfiles_map object

        Provides the ability to iterate through dirpath, dirnames,
        filenames acquired from os.walk.
    """
    def elements(self) -> Iterable[WalkNode]:
        yield from self.walk

    def filter(self, element: WalkNode):
        if self.filter_func:
            return self.filter_func(*element)

        return True

class map_dirs(get_dirs, subfiles_map[WalkNode]):
    """ map_dirs(func, root=os.path.curdir,
        depth=contains_all(), limit=None, filter=None)
        --> subfiles_map object

        Maps the arguments dirpath, dirnames, filenames acquired from
        os.walk to the input function.

        Input function must be:
            func(dirpath, dirnames, filename)
    """

    def process(self, element: WalkNode):
        return self.func(*element)


class get_elements(subfiles_get[str]):
    """ get_elements(root=os.path.curdir,
        depth=contains_all(), limit=None, filter=None)
        --> subfiles_map object

        Provides the ability to iterate through the name of an element
        (file or directory) in the root folder or its subdirectories.
    """
    def elements(self) -> Iterable[str]:
        for dirpath, dirnames, filenames in self.walk:
            for dirname in dirnames:
                yield os.path.join(dirpath, dirname)
            for filename in filenames:
                yield os.path.join(dirpath, filename)


class map_elements(get_elements, subfiles_map[str]):
    """ map_elements(func, root=os.path.curdir,
        depth=contains_all(), limit=None, filter=None)
        --> subfiles_map object

        Maps the name of an element (file or directory) to the input
        function.

        Input function must be:
            func(dirpath, element)
    """
    pass
