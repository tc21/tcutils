# coding:utf-8
from tc.utils import is_cjk_fullwidth


"""
The original document was crated by me for python 2 at an unknown date.
Rewritten for python 3 on 1 April 2018.
- Tianyi Cao

The purpose of this script is to generate an html with <ruby> tags to
correctly display Japanese or Chinese text (originally intended for lyrics)
with their phonetic spelling above the text.

split_for_ruby(lyrics) generates takes text (no newlines, | indicate newline)
and creates a ruby-ready html document for someone to fill in the actual
phonetics

split_to_ruby(lyrics, title, startSign, endSign, newLineSign) takes text
(no newlines, newLineSign(default "|") indicates newline; startSign and
endSign(default "(" and ")") indicate phonetics)and creates a ruby-ed html
document so you can view and print!

delete_ruby(lyrics, startSign, endSign) just deletes everything between the
two signs, effectively eliminating any phonetics the lyrics may contain.
"""


def split_for_ruby(input_):
    result = ""
    result += "<ruby>"
    for char in input_:
        if char == "|":
            result += "</ruby>\n<br>\n<ruby>"
        else:
            result += "" + char + "	<rt></rt>"
    result += "</ruby>"
    return result


def split_to_ruby(lyric, title, start_char="(", end_char=")", newline_char="|"):
    # Designed for Japanese, although Chinese should work as well
    result = f"""
        <meta http-equiv='Content-Type' content='text/html; charset=utf-8'>
            <style type='text/css'>
                * {{font-family:'Helvetica Neue', 'Helvetica', sans-serif;}}
                div {{margin:6%;}}
                ruby {{font-size:16px;}}
                rt {{font-size:10px;font-weight:500;}}
            </style>
            <title>{title}</title>
            <div>
                <ruby>
                    <em>{title}</em>
                </ruby>
                <br>
                <br>
    """

    while len(lyric) != 0:
        if lyric[0] == newline_char:
            _, lyric = lyric
            result += """
                <ruby>
                    &nbsp;
                    <rt>&nbsp;</rt>
                </ruby>
                <br>
            """
            print("NEWLINE")
        elif is_cjk_fullwidth(lyric[0]):
            print("---")
            print(lyric)
            start_position = lyric.find(start_char)
            end_position = lyric.find(end_char)
            character = lyric[0:start_position]
            ruby = lyric[start_position+1:end_position]
            result += f"""
                <ruby>
                    {character}
                    <rt>{ruby}</rt>
                </ruby>
            """
            print("CJKFW")
            print(start_position, end_position)
            lyric = lyric[end_position+1:]
        else:
            # It's just a normal character
            result += lyric[0]
            lyric = lyric[1:]
            print("NC")
    result += "</div>"
    return result


def delete_ruby(lyric, start_char="(", end_char=")", newline_char="|"):
    result = ""
    while len(lyric) != 0:
        if lyric[0] == newline_char:
            result += "\n"
            lyric = lyric[1:]
        elif ord(lyric[0]) > 12543 and ord(lyric[0]) < 65000:
            startSignPosition = lyric.find(start_char)
            endSignPosition = lyric.find(end_char)
            character = lyric[0:startSignPosition]
            # ruby = lyric[startSignPosition + 1:endSignPosition]
            result += character
            lyric = lyric[endSignPosition + 1:]
        else:
            # It's just a normal character
            result += lyric[0]
            lyric = lyric[1:]
    return result
