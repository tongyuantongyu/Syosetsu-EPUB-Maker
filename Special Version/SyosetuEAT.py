# coding:utf-8

import requests
from bs4 import BeautifulSoup
from multiprocessing.dummy import Pool as tp
import os
from ebooklib import epub
import base64
import time
import random
import cchardet

pool = tp(processes=8)
dirn = os.getcwd()
hd = {'User-Agent': 'Mozilla/5.0 (MSIE 9.0; Windows NT 6.1; Trident/5.0)'}
p = {"http": "http://127.0.0.1:8080"}
style = b'CkBuYW1lc3BhY2UgZXB1YiAiaHR0cDovL3d3dy5pZHBmLm9yZy8yMDA3L29wcyI7CmJvZHkgewogICAgZm9udC1mYW1pbHk6IENhbWJyaWEsIExpYmVyYXRpb24gU2VyaWYsIEJpdHN0cmVhbSBWZXJhIFNlcmlmLCBHZW9yZ2lhLCBUaW1lcywgVGltZXMgTmV3IFJvbWFuLCBzZXJpZjsKfQpoMiB7CiAgICAgdGV4dC1hbGlnbjogbGVmdDsKICAgICB0ZXh0LXRyYW5zZm9ybTogdXBwZXJjYXNlOwogICAgIGZvbnQtd2VpZ2h0OiAyMDA7ICAgICAKfQpvbCB7CiAgICAgICAgbGlzdC1zdHlsZS10eXBlOiBub25lOwp9Cm9sID4gbGk6Zmlyc3QtY2hpbGQgewogICAgICAgIG1hcmdpbi10b3A6IDAuM2VtOwp9Cm5hdltlcHVifHR5cGV+PSd0b2MnXSA+IG9sID4gbGkgPiBvbCAgewogICAgbGlzdC1zdHlsZS10eXBlOnNxdWFyZTsKfQpuYXZbZXB1Ynx0eXBlfj0ndG9jJ10gPiBvbCA+IGxpID4gb2wgPiBsaSB7CiAgICAgICAgbWFyZ2luLXRvcDogMC4zZW07Cn0K'

try:
    cor = open('correct.txt', 'rb').read()
    cor = cor.decode(cchardet.detect(cor)['encoding'])
    replacedlist = eval(cor)
    corr = True
except:
    corr = False


def correct(st):
    if corr is True:
        for i in replacedlist:
            st = st.replace(i[0], i[1])
    return st


def getpage(link):
    print('Getting: ' + link)
    gethtml = requests.get(link, headers=hd, proxies=p)
    Soup = BeautifulSoup(gethtml.content, 'lxml')
    return Soup


def getpage2(link):
    print('Getting: ' + link[0])
    i = 0
    while i < 3:
        try:
            gethtml = requests.get(link[1], headers=hd, proxies=p)
            if gethtml.status_code == 200:
                print('Get: ' + link[0] + ' Status ' + str(gethtml.status_code) + '. Succeed.')
                break
            else:
                print('Get: ' + link[0] + 'Status' + str(gethtml.status_code) + '. Retry...')
                i += 1
        except:
            print('Get: ' + link[0] + ' An Error occured. Retry...')
            i += 1
    Soup = BeautifulSoup(gethtml.content, 'lxml')
    time.sleep(random.uniform(5, 20))
    return (link[0], Soup)


def makehtml(i):
    tit = i.find('p', class_="novel_subtitle").get_text()
    tit = correct(tit)
    con = i.find('div', id="novel_honbun", class_="novel_view").prettify()
    con = correct(con)
    html = '<html>\n<head>\n' + '<title>' + tit + '</title>\n</head>\n<body>\n<div>\n<h3>' + tit + '</h3>\n' + con + '</div>\n</body>\n</html>'
    print('Page read. Title: ' + tit)
    return (tit, html)


def getmake(link):
    h = getpage2(link)
    return (link[0], makehtml(h[1]))


syoid = input('Enter Novel ID of the novel: ')
menupage = getpage('http://ncode.syosetu.com/' + syoid + '/')
firstpage = getpage('http://ncode.syosetu.com/' + syoid + '/1/')
author = menupage.find('div', class_="novel_writername").get_text().split('：')[-1]
pagenum = int(firstpage.find('div', id='novel_no').get_text().split('/')[-1])
maintitle = menupage.find('title').get_text().split(' - ')[0] + ' - エキサイト翻訳'
about = menupage.find("div", id="novel_ex").prettify()
print('Started. Title: ' + maintitle)
if menupage.find('div', class_="chapter_title") is None:
    worklist = [(str(i), 'http://www.excite-webtl.jp/world/chinese/web/body/?wb_url=http://ncode.syosetu.com/' + syoid + '/' + str(i) + '/&wb_lp=JACH&wb_dis=0&big5=no') for i in range(1, pagenum + 1)]
    hl = pool.map(getmake, worklist)
    book = epub.EpubBook()
    book.set_identifier(syoid)
    book.set_title(maintitle)
    book.set_language('jp')
    book.add_author(author)
    sabout = '<html>\n<head>\n<title>小説紹介</title>\n</head>\n<body>\n<div>\n<h3>小説紹介</h3>\n' + about + '</div>\n</body>\n</html>'
    cabout = epub.EpubHtml(title='About', file_name='0.xhtml', content=sabout, lang='ja_jp')
    book.add_item(cabout)
    conlist = [epub.EpubHtml(title=i[1][0], file_name=i[0] + '.xhtml', content=i[1][1], lang='ja_jp') for i in hl]
    for i in conlist:
        book.add_item(i)
    contuple = conlist
    contuple.insert(0, 'cabout')
    contuple = tuple(contuple)
    book.toc = (epub.Link('0.xhtml', '小説紹介', 'intro'), (epub.Section('目録：'), contuple))
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    dstyle = str(base64.b64decode(style))
    css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=dstyle)
    book.add_item(css)
    book.spine = ['nav'] + conlist
    epub.write_epub(dirn + '\\' + maintitle + '.epub', book, {})
    print('Succeed.')
else:
    book = epub.EpubBook()
    book.set_identifier(syoid)
    book.set_title(maintitle)
    book.set_language('jp')
    book.add_author(author)
    sabout = '<html>\n<head>\n<title>小説紹介</title>\n</head>\n<body>\n<div>\n<h3>小説紹介</h3>\n' + about + '</div>\n</body>\n</html>'
    cabout = epub.EpubHtml(title='About', file_name='0.xhtml', content=sabout, lang='ja_jp')
    catalog = menupage.find('div', class_='index_box').find_all(["div", "dd"], class_=['chapter_title', 'subtitle'])
    book.add_item(cabout)
    worklist = [[]]
    j = 0
    for i in catalog:
        if i.name == 'div':
            worklist.append([i.get_text(), []])
            j += 1
        if i.name == 'dd':
            if j == 0:
                num = i.find('a')['href'].split('/')[-2]
                worklist[0].append((num, 'http://www.excite-webtl.jp/world/chinese/web/body/?wb_url=http://ncode.syosetu.com/' + syoid + '/' + num + '/&wb_lp=JACH&wb_dis=0&big5=no'))
            else:
                num = i.find('a')['href'].split('/')[-2]
                worklist[j][1].append((num, 'http://www.excite-webtl.jp/world/chinese/web/body/?wb_url=http://ncode.syosetu.com/' + syoid + '/' + num + '/&wb_lp=JACH&wb_dis=0&big5=no'))
    pagelist = [cabout]
    numlist = []
    for k in range(len(worklist)):
        i = worklist[k]
        if k == 0 and len(i) != 0:
            plist = pool.map(getpage2, i)
            hl = []
            for j in range(len(plist)):
                h = makehtml(plist[j][1])
                num = str(k) + ' - ' + str(j + 1)
                pag = epub.EpubHtml(h[0], file_name=num + '.xhtml', content=h[1], lang='ja_jp')
                book.add_item(pag)
                pagelist.append(pag)
                hl.append((h[0], num))
            numlist.append(hl)
        elif k == 0 and len(i) == 0:
            numlist.append([])
            pass
        elif isinstance(i[1], list):
            plist = pool.map(getpage2, i[1])
            hl = []
            for j in range(len(plist)):
                num = str(k) + ' - ' + str(j + 1)
                h = makehtml(plist[j][1])
                pag = epub.EpubHtml(h[0], file_name=num + '.xhtml', content=h[1], lang='ja_jp')
                book.add_item(pag)
                pagelist.append(pag)
                hl.append((h[0], num))
            numlist.append([i[0], hl])
    toclist = [epub.Link('0.xhtml', '小説紹介', 'intro')]
    if numlist[0] != []:
        for i in numlist[0]:
            toclist.append(epub.Link(i[1] + '.xhtml', i[0], i[1]))
    for i in numlist[1:]:
        intuple = tuple([epub.Link(j[1] + '.xhtml', j[0], j[1]) for j in i[1]])
        toclist.append((epub.Section(i[0]), intuple))
    book.toc = tuple(toclist)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    dstyle = str(base64.b64decode(style))
    css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=dstyle)
    book.add_item(css)
    book.spine = ['nav'] + pagelist
    epub.write_epub(dirn + '\\' + maintitle + '.epub', book, {})
    print('Succeed.')
    input()
