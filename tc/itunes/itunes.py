
from __future__ import annotations

import win32com.client
import win32ui
import pythoncom
import ctypes
import sys
import pickle
import os.path
from typing import List, Generator, Callable, Optional
from dataclasses import dataclass


_pickle_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           './itunes_tracks.pickle')


_ITPlaylistSearchFieldAll = 0
_ITPlaylistSearchFieldVisible = 1
_ITPlaylistSearchFieldArtists = 2
_ITPlaylistSearchFieldAlbums = 3
_ITPlaylistSearchFieldComposers = 4
_ITPlaylistSearchFieldSongNames = 5

_ITPlaylistRepeatModeOff = 0
_ITPlaylistRepeatModeOne = 1
_ITPlaylistRepeatModeAll = 2


class iTunes:
    def __init__(self):
        self.itunes = _get_itunes()

    def search(self, text: str, search_field = _ITPlaylistSearchFieldVisible) -> Optional[iTunesObjectCollection]:
        collection = self.itunes.LibraryPlaylist.Search(text, search_field)

        if collection is None:
            return None

        return iTunesObjectCollection(collection)

    def search_all(self, text: str) -> Optional[iTunesObjectCollection]:
        return self.search(text, _ITPlaylistSearchFieldAll)

    def search_visible(self, text: str) -> Optional[iTunesObjectCollection]:
        return self.search(text, _ITPlaylistSearchFieldVisible)

    def search_artists(self, text: str) -> Optional[iTunesObjectCollection]:
        return self.search(text, _ITPlaylistSearchFieldArtists)

    def search_albums(self, text: str) -> Optional[iTunesObjectCollection]:
        return self.search(text, _ITPlaylistSearchFieldAlbums)

    def search_composers(self, text: str) -> Optional[iTunesObjectCollection]:
        return self.search(text, _ITPlaylistSearchFieldComposers)

    def search_songs(self, text: str) -> Optional[iTunesObjectCollection]:
        return self.search(text, _ITPlaylistSearchFieldSongNames)

    @property
    def playlists(self) -> iTunesPlaylistCollection:
        collection = self.itunes.LibrarySource.Playlists
        return iTunesPlaylistCollection(collection)

    def get_playlist(self, name: str) -> Optional[iTunesPlaylist]:
        for playlist in self.playlists:
            if playlist.name.lower() == name.lower():
                return playlist

        return None

    def current_song(self) -> Optional[iTunesTrack]:
        track = self.itunes.CurrentTrack
        if track is None:
            return None

        return _make_track(track)


def com_property(name: str, com_name: str, setter=True):
    def class_decorator(cls):
        def get_property(self):
            return getattr(self.object, com_name)
        def set_property(self, value):
            setattr(self.object, com_name, value)
        if setter:
            setattr(cls, name, property(get_property, set_property))
        else:
            setattr(cls, name, property(get_property))
        return cls
    return class_decorator


@com_property('name', 'Name')
class iTunesObject:
    def __init__(self, object):
        self.object = object


class iTunesObjectCollection:
    def __init__(self, collection):
        self.collection = collection

    def __len__(self):
        return self.collection.Count

    def __getitem__(self, index: int):
        return self.collection.Item(index + 1)


class iTunesPlaylistCollection(iTunesObjectCollection):
    def __getitem__(self, index: int) -> iTunesPlaylist:
        item = super().__getitem__(index)
        return iTunesPlaylist(item)


@com_property('shuffle', 'Shuffle')
@com_property('repeat', 'SongRepeat')
class iTunesPlaylist(iTunesObject):
    def __init__(self, playlist: 'IITPlaylist'):
        super().__init__(playlist)

    def play(self, shuffle=False, repeat=_ITPlaylistRepeatModeAll):
        self.shuffle = shuffle
        self.repeat = repeat
        self.object.PlayFirstTrack()


@dataclass
class iTunesTrack:
    name: str
    artist: str = ''
    album: str = ''
    genre: str = ''
    lyrics: str = ''

    def contains_lyrics(self, lyrics: str) -> bool:
        '''
        You might think this is very inefficent. You are right: I measured this function and its
        runtime is 535 (!) times the trivial 'return lyrics in self.lyrics'

        Its average runtime increases from 215ns to 115μs, meaning the time to seach my 868-song
        library increases from (factoring in the overhead of the program, but not the overhead
        of starting the program) 6ms to 106ms.

        Consider how often you need to search your iTunes library for a song by lyrics.
        Don't waste time optimizing things you don't have to optimize.
        '''
        search_lyrics = ''.join(c for c in self.lyrics if c.isalpha()).lower()
        search_term = ''.join(c for c in lyrics if c.isalpha()).lower()

        return search_term in search_lyrics

    def play(self):
        _play_song(self.name)

    def __str__(self):
        if self.artist == '':
            return self.name

        return f'{self.artist} - {self.name}'

    def __repr__(self):
        return (f'iTunesTrack(name={repr(self.name)}, artist={repr(self.artist)}, '
                f'album={repr(self.album)}, genre={repr(self.genre)})')


def _get_itunes() -> 'IiTunes':
    pythoncom.CoInitialize()
    itunes = win32com.client.Dispatch('iTunes.Application')
    return itunes


def _iter_songs() -> Generator['IITFileOrCDTrack', None, None]:
    tracks = _get_itunes().LibraryPlaylist.Tracks
    count = tracks.Count

    for i in range(1, count + 1):  # 1-indexed
        raw_track = tracks.Item(i)
        if raw_track.Kind != 1:
            continue

        track = win32com.client.CastTo(raw_track, 'IITFileOrCDTrack')
        if track.Podcast:
            continue
        yield track


def _make_track(track: 'IITFileOrCDTrack') -> iTunesTrack:
    arguments = track.Name, track.Artist, track.Album, track.Genre, track.Lyrics
    return iTunesTrack(*arguments)


def _play_song(name: str):
    tracks = _get_itunes().LibraryPlaylist.Tracks
    track = tracks.ItemByName(name)
    if track is None:
        raise ValueError(f'song does not exist: \'{name}\'')

    track.Play()


def all_songs(cached=True) -> List[iTunesTrack]:
    ''' warning: VERY SLOW when not cached '''
    if cached:
        try:
            return pickle.load(open(_pickle_file, 'rb'))
        except (FileNotFoundError, EOFError, pickle.UnpicklingError) as e:
            print(f'unable to unpickle file: {e}')
            print(f'using uncached version instead...')

    print('warning: uncached version is very slow!')

    tracks = []
    for i, song in enumerate(_iter_songs()):
        if i % 20 == 0:
            print(f'{i} songs retrieved...')
        tracks.append(_make_track(song))

    print(f'all songs retrieved')
    pickle.dump(tracks, open(_pickle_file, 'wb'))
    return tracks


def search_lyrics(lyrics: str, cached=True) -> List[iTunesTrack]:
    tracks = all_songs(cached)
    return [t for t in tracks if t.contains_lyrics(lyrics)]


# bonus function
def play_first_with_lyrics(l: str) -> bool:
    songs = list(search_lyrics(l))
    if songs != []:
        songs[0].play()
