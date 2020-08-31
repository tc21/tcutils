from .lyrics import convert_ruby

'''
The following is copied from this modules design description,
originally created by me on 1 April 2018.


Plain text lyrics:

A UTF-8 encoded file with custom syntax inspired by markdown. It should provide
a framework of compiling text into html.

Each line of lyrics will be on its own line, with the result closely resembling
the original file.

All characters are allowed and unless specified rendered as text.


Syntax:

- Header
    One header is allowed per file. If a single line containing only "="
    is present, then all lines above that line is the header.

    The first line in the header is the title, while subsequent lines are
    the artist, album name, etc. They are simply "additional information"
    and can be anything.

- Body
    Phonetic spellings:
        Indicated by [text](phonetics). The phonetics are rendered above the
        text using HTML ruby. The square brackets around the text can be
        omitted, and the text will be inferred to the best ability of the
        compiler [Note 1].
    Sections:
        Indicated by a "#" at the beginning of the line. This line should be
        less noticable than the lyrics.


This document does not define styling or comments. These can be added in a
custom implementation.


Compiled html:

As a guidance, this document provides the following html structure and some
suggested styling:

<!doctype html>
<html>
    <head>
        <meta charset="utf-8">
        <style>
            body {
                font-family: 'Hiragino Kaku Gothic Pro', 'Osaka', 'Meiryo', 'MS PGothic',
                             'Segoe UI', 'Helvetica Neue', -apple-system, sans-serif;
                margin: 24px;
            }
            h1 { font-size: 22px; }
            h2 { font-size: 14px; }
            h3 { font-size: 12px; color: gray; }
            rt { font-size: 10px; };
            #header { margin-bottom: 12px; }
            #content { margin-top: 12px; }
            #header > *, #content > * { margin: 0; }
            .line { font-size: 16px; line-height: 40px; }
            .space { height: 24px; }
        </style>
        <title>TITLE</title>
    </head>
    <body>
        <div id="header">
            <h1>TITLE</h1>
            <h2>ARTIST - ALBUM</h2>
        </div>
        <div id="content">
            <div class="line">
                A test line with some <ruby>phonetic spellings<rt>HTML RUBY</rt></ruby>.
            </div>
            <div class="space"></div>
            <h3>SEP</h3>
            <div class="line">
                A second test line.
            </div>
        </div>
    </body>
</html>
'''
