""" The subfiles module provides the ability to iterate through all
    files or folders in a directory and its subdirectories. """

from .comic import Comic, Token, get_info, organize
from .subcomics import SubcomicSpecification, organize_subcomics, organize_subcomics_with_artists
