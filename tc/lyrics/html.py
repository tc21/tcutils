'''
The suggested html structure reproduced here for convenience

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


def word(text, ruby=None):
    if ruby is None:
        return text
    else:
        return f'<ruby>{text}<rt>{ruby}</rt></ruby>'


def line(inner=None):
    if inner is None:
        return '<div class="space"></div>'
    else:
        return f'<div class="line">\n    {inner}\n</div>'


def space():
    return '<div class="space"></div>'


def content(inner=None):
    result = '<div id="content">'
    for line in inner.split('\n'):
        result += '\n    ' + line
    result += '\n</div>'
    return result


def header(title, info=None):
    result = f'''<div id="header">
    <h1>{title}</h1>'''
    if info is not None and len(info) > 0:
        for line in info.split('\n'):
            result += f'\n    <h2>{line}</h2>'
    result += '\n</div>'
    return result


def html(title, header, content):
    result = '''<!doctype html>
<html>
    <head>
        <meta charset="utf-8">
        <style>
            body {
                font-family: 'Hiragino Kaku Gothic Pro', 'Osaka', 'Meiryo', 'MS PGothic',
                             'Segoe UI', 'Helvetica Neue', -apple-system, sans-serif;
                margin: 3% 6%;
            }
            h1 { font-size: 22px; }
            h2 { font-size: 14px; }
            h3 { font-size: 12px; color: gray; }
            rt { font-size: 10px; };
            #header { margin-bottom: 24px; }
            #content { margin-top: 24px; }
            #header > *, #content > * { margin: 0; }
            .line { font-size: 16px; line-height: 40px; }
            .space { height: 24px; }
        </style>
        <title>''' + title + '''</title>
    </head>
    <body>'''
    for line in header.split('\n'):
        result += '\n        ' + line
    for line in content.split('\n'):
        result += '\n        ' + line
    result += '''
    </body>
</html>\n'''
    return result
