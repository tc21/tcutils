import os
import re
import subprocess
import random
from send2trash import send2trash


def auto_merge(path='.', ext='flv', trash=False, test=False):
    """ Merges files 12345678-1.flv, ..., 12345678-12.flv into a single file.
        Assumes macOS, since Bilibili Mac only works on macOS.
    """
    files = [file for file in os.listdir(path) if file.endswith(ext)]
    match = None
    matched_files = []

    for file in files:
        match = re.search(r'^(\D*\d+)([-_\ ])([01])\2(.*?)\.([^\.]+)$', file)
        if match is not None:
            matched_files = [os.path.join(path, file)]
            break
    else:
        print('Could not find first file to merge')
        return

    key_name, separator, first_index, description_name, ext = match.groups()

    def matches():
        index = int(first_index)
        while True:
            index += 1
            yield (r'^' + re.escape(key_name + separator + str(index)) +
                   r'.*' + re.escape('.' + ext) + r'$')

    for next_match in matches():
        for file in files:
            match = re.search(next_match, file)
            if match is not None:
                matched_files.append(os.path.join(path, file))
                break
        else:
            print('Could not find next file in serial, finishing...')
            break

    output_basename = (key_name if len(description_name) == 0 else
                       f'{description_name} ({key_name})')
    output_name = os.path.join(path, output_basename + '.' + ext)

    if test:
        print('\n'.join(matched_files))
        print('> ' + output_name)
        return

    merge(matched_files, output_name, trash)


def merge(files, dest, trash=False):
    if len(files) <= 1:
        print(f'{len(files)} cannot be merged, exiting...')
        return
    # We use a random number to prevent filename collisions just in case
    # Why this way? Who knows, but the original code did this
    random_seed = random.randint(1000, 65535)
    temp_file = f".temp{random_seed}~files.txt"
    with open(temp_file, "w", encoding="utf-8") as temp:
        for file in files:
            temp.write(f"file '{file}'\n")

    ext = os.path.splitext(files[0])[-1]
    if (os.path.splitext(dest)[-1] != ext):
        dest = dest + '.' + ext

    print(f'Merging {len(files)} files into {dest}...')
    subprocess.call(["ffmpeg", "-f", "concat", "-i", temp_file, "-c", "copy",
                     dest])
    os.remove(temp_file)

    if trash:
        print(f'Removing split files...')
        for file in files:
            send2trash(file)


def rename(path='.', auto=True, name=None):
    """ Converts directory names from
            example: 樱花任务 / 第2话 集结的五位勇者 番剧 bilibili 哔哩哔哩弹幕视频网
        to
            example: 2 集结的五位勇者

        Specify auto=False and name if there are multiple shows in the
        same directory.
    """
    assert auto or name is not None, "Must provide name or use auto mode"
    END = " 番剧 bilibili 哔哩哔哩弹幕视频网"
    SEP = "话 "
    START = " : 第"
    if not auto:
        START = name + START
    dirs = [path + "/" + d for d in os.listdir(path)]
    for d in dirs:
        start_index = d.find(START)
        if os.path.isdir(d) and start_index > 0:
            number_start = start_index + len(START)
            number_end = d.find(SEP)
            name_start = number_end + len(SEP)
            name_end = d.find(END)
            os.rename(d, path + "/" + d[number_start:number_end] + " " + d[name_start:name_end])
