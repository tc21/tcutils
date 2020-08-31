import re
import datetime
import urllib.request
from . import caching
import bs4
from urllib.error import URLError
import requests

from typing import Dict, Any, Optional

_code = 'code'
_maker = 'maker'
_title = 'title'
_releasedate = 'release_date'
_imagelink = 'image_link'
_agerestriction = 'age_restriction'
_description = 'description'
_taglist = 'tags'
_tag = 'tag'
_downloadlinklist = 'download_links'
_downloadlink = 'download_link'
_sampleimages = 'sample_images'
_voice = 'voice'


def site_link(code: str) -> str:
    return f'https://www.dlsite.com/maniax/work/=/product_id/RJ{code:0>6}.html'


def process_html(text: str) -> str:
    # remove html word-breaks, mainly because of 4chan
    text = text.replace('<wbr>', '')
    # replace non-breaking spaces so the next line works properly
    text = text.replace('&nbsp;', chr(160))
    # remove preceding whitespace and trailing newlines
    return re.compile(r'\n\s+(?=<)|(?<=>)\s+').sub('', text)


def get_info(code: str) -> Dict[str, Any]:
    ''' Using BeautifulSoup, scrape dlsite.com to get
        work info for a particular work. '''

    try:
        site = urllib.request.urlopen(site_link(code))
        site_data = site.read().decode('utf-8')
    except URLError:
        print(f'Error: Could not access {site_link(code)}')
        return {}

    site_data = process_html(site_data)

    page = bs4.BeautifulSoup(site_data, 'html.parser')

    info: Dict[str, Any] = {_code: code}

    # from the main (big) title
    info[_title] = str(list(page.find(id='work_name').strings)[-1])

    # from the サークル名 field
    info[_maker] = str(page.find(id='work_maker').find('span', class_='maker_name').string)

    # a meta tag in the header
    info[_imagelink] = page.find('meta', attrs={'name': 'twitter:image:src'})['content']

    # test
    image_slider_component = page.find(id='work_left').find('div', attrs={'data-vue-component': 'product-slider'})
    sample_images = []
    for image_slider_data in image_slider_component.find('div').find('div').find_all('div'):
        sample_images.append('https:' + image_slider_data.attrs['data-src'])
    info[_sampleimages] = sample_images

    # parsed from the 販売日 field
    releasedate_string = page.find('a', href=re.compile(r'dlsite.com/\w+/new/=/year/\d+/mon/\d+/day/')).string
    releasedate_string = releasedate_string[:releasedate_string.find('日')+1]
    info[_releasedate] = datetime.datetime.strptime(releasedate_string, '%Y年%m月%d日').date()  #note: datetime object

    # parsed from the 年齢指定 field
    agerestriction_string = page.find('div', attrs={'class': 'work_genre'}).string
    agerestriction_match = re.search(r'\d+', agerestriction_string)
    info[_agerestriction] = int(agerestriction_match.group()) if agerestriction_match is not None else 0

    # parsed from the ジャンル field
    info[_taglist] = list(map(str, page.find('div', attrs={'class': 'main_genre'}).strings))

    # parsed from the 作品内容 section
    desc_container = page.find('div', attrs={'class': 'work_parts_container', 'itemprop': 'description'})
    info[_description] = read_text(desc_container)

    work_right = page.find('div', attrs={'id': 'work_right'})
    cast_text = work_right.find(text='声優')
    if cast_text is not None:
        info[_voice] = [e.string for e in cast_text.parent.parent.findAll('a')]

    if info[_title] is None or info[_title] == '':
        print(f'Error: Could not fetch complete work info for RJ{code}')
        return {}

    ''' This is a brief recreation of the dlsite site structure (written
        Jan. 3, 2017) to understand how I am scraping the site, so that later I
        may change the code. Useful parts are {marked} with braces.

        Head:
        <head>
            <meta name="keywords" content="{}" />  (unused)
                (where {} is a comma-delimited list of the work name, and then
                 the circle name, and then the work's tags; I didn't use this
                 because I wasn't sure how reliable it is)

            <meta name="twitter:image:src" content="{}" />  (used)
                (where {} is a link to the work's cover image, exactly 560x420
                 pixels)

            <meta property="og:description" content="{}" />  (unused)
                (where {} is a really useful one-line description of the work)

            <meta property="og:image" content="{}" />  (unused)
                (where {} is a link to the work's thumbnail image, exactly
                 100x100 pixels)

        </head>

        Elements identified by id:
        <h1#work_name>
            <a href itemprop="url">{}/a>
                (where {} is the title of the work)

        </h1>

        <table#work_maker>
            (contains several tags, including circle name)

        <table#work_outline>
            (contains several tags, including (if applicable):
                release date, last updated, series name, age restriction, work
                type, file type, operating system, other notices, events,
                tags/genres)


        <div#main_inner>
            <div.work_article.work_story>
                {the description of the work, contained in the 'work info'
                 section}
            </div>
        </div>
    '''

    return info


def read_text(tag: bs4.Tag) -> str:
    ''' Using BeautifulSoup,
        read the text contained in a tag as plain text. '''
    text = ''

    item: bs4.Tag
    for item in tag.contents:
        if item.name is None:
            text += item.string
        elif item.name == 'br' and item.contents == []:
            text += '\n'
        else:
            text += read_text(item)

    return text


def get_search_suggestions(search_term: str) -> Dict[str, Any]:
    ''' Calls the dlsite api with a search term and returns suggestions.
        Returns a json file with the following structure:
        ```
        {
            work: [<list of works>]
            maker: [<list of makers>]
            reqtime: <copy of argument 'time'>
        }
        ```
        work[]:
        ```
        {
            work_name: str = 'name of the work'
            workno: str = 'RJ123456'
            maker_name: str = 'name of the maker'
            maker_id: str = 'RG12345'
            work_type: str = '3-letter work type-indicator'
            intro_s: str = 'sort description'
            age_category: int = 'enum: 3 is R-18, others unknown'
            is_ana: bool = 'purpose unknown'
        }
        ```
        maker[]:
        ```
        {
            workno: str = 'workno from work[]'
            maker_name: str = 'name of the maker'
            maker_name_kana: str = 'katakana name'
            maker_id: str = 'RG12345'
            age_category: int = 'same as above'
        }
        ```
    '''
    timestamp = int(datetime.datetime.now().timestamp() * 1000)
    response = requests.get(
        f'https://www.dlsite.com/suggest?term={search_term}&site=adult-jp&time={timestamp}'
    )
    return response.json()

def find_code(name: str) -> Optional[str]:
    ''' Given a name, attempts to find the 6-digit rj-code for a work matching the name '''
    suggestions = get_search_suggestions(name)
    if suggestions is not None and suggestions.get('work', []) != []:
        workno = suggestions['work'][0]['workno']
        if len(workno) == 8:
            return workno[2:]

    return None
