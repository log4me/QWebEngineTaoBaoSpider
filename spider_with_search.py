#!/usr/bin/env python3
# coding=utf-8

from PyQt5.QtCore import QObject, QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineDownloadItem
from PyQt5.QtCore import QUrl
from config import config as cfg
from config import js
from urllib.parse import parse_qs, urlparse, quote
import os


def singleShot(time, func, param):
    def fun():
        func(*param)
    QTimer.singleShot(time, fun)


class SaveAsSpider(QWebEngineView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.page().profile().setHttpUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36')
        self.loadFinished.connect(self.process_load_finished)
        self.page().profile().downloadRequested.connect(self.process_download_request)
        self.url_list = self.read_save_url_list(cfg['URL_LIST_FILE'])
        self.current_url_indx = cfg['START_URL_INDX']
        self.MAX_URL_INDX = len(self.url_list)
        self.SAVE_DIR = cfg['SAVE_DIR']
        self.is_downloading = False
        if not os.path.exists(self.SAVE_DIR):
            os.mkdir(self.SAVE_DIR)
        self.sleeping = False
        self.is_pausing = False
        # self.timer = MyTimer(self)

    def process_download_finished(self):
        self.is_downloading = False
        print("downloading finished.")

    def process_timer_finished(self):
        if self.is_downloading:
            QTimer.singleShot(2000, self.process_timer_finished)
        else:
            pass
            self.goto_next_page()


    def process_load_finished(self, status):
        # 1. slide down to load full page
        scroll_count = 0
        while scroll_count < 10:
            self.page().runJavaScript("window.scrollBy(0, 1000)")
            # time.sleep(random.randint(1, 3))
            # time.sleep(0.5)
            scroll_count += 1
        # 2. save page as complete mhtml file
        # this can save page as a mhtml file which contains the web file and resource file
        self.is_downloading = True
        self.page().save(os.path.join(self.SAVE_DIR, self.url_list[self.current_url_indx][0] + ".mhtml"), format=QWebEngineDownloadItem.MimeHtmlSaveFormat)
        # this can save page as a html file and a directory with resources
        QTimer.singleShot(2000, self.process_timer_finished)
        # TODO. handle error during get page

    def goto_next_page(self):
        if self.is_pausing:
            return
        # 3. load next url into page
        self.current_url_indx += 1
        if self.current_url_indx < self.MAX_URL_INDX:
            self.load(QUrl(self.url_list[self.current_url_indx][1]))
        else:
            print("detail page save success")
            if self.MAX_URL_INDX < len(self.url_list):
                self.write_url_back()
                self.MAX_URL_INDX = len(self.url_list)
                self.load(QUrl(self.url_list[self.current_url_indx]))
            else:
                self.sleeping = True

    def add_url(self, url_list):
        self.url_list.extend(self.parse_url_id(url_list))

    def process_download_request(self, item):
        item.finished.connect(self.process_download_finished)
        print("save {} to {}".format(item.url(), item.path()))
        item.accept()

    def read_save_url_list(self, filename):
        res = []
        with open(filename) as f:
            for line in f:
                res.append(line)
        return self.parse_url_id(res)

    def parse_url_id(self, url_list):
        res = []
        for url in url_list:
            # parse id from url as the save filename
            id = parse_qs(urlparse(url).query).get('id', None)
            if id is not None:
                res.append((id[0], url))
        return res

    def start_craw(self):
        if self.current_url_indx < self.MAX_URL_INDX:
            self.load(QUrl(self.url_list[self.current_url_indx][1]))
        else :
            print('START_URL_INDX > number of urls')
            if self.MAX_URL_INDX < len(self.url_list):
                self.MAX_URL_INDX = len(self.url_list)
                self.load(QUrl(self.url_list[self.current_url_indx][1]))
            else:
                self.sleeping = True

    def write_url_back(self):
        with open(cfg['URL_LIST_WRITE_BACK_FILE'], 'w') as f:
            for url in self.url_list:
                f.write(url[1])
                if url[-1] != '\n':
                    f.write('\n')
    def pause(self):
        self.is_pausing = True

    def cont(self):
        self.is_pausing = False
        self.goto_next_page()

DetailSpider = SaveAsSpider

class SearchSpider(QWebEngineView):
    def __init__(self, detailspider, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.page().profile().setHttpUserAgent('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36')
        self.page().loadFinished.connect(self.process_load_finished)
        self.detailspide = detailspider
        self.keywords = cfg['KEY_WORDS']
        self.current_key_words_indx = cfg['START_KEYWORD']
        self.current_page = 0
        self.LIMIT_PAGE_INDX = cfg['MAX_PAGE']
        self.max_page = self.LIMIT_PAGE_INDX
        self.MAX_KEY_WORD_INDX = len(self.keywords)
        self.search_base_url = cfg['SEARCH_BASE_URL']
        self.max_page_from_page = self.LIMIT_PAGE_INDX
        # flag to judge search spider status
        self.is_getting_max_page = False
        self.max_page_got = False



        self.judging_captcha = False

        self.is_pausing = False
        self.has_captcha = False


    def process_load_finished(self, status):
        if status:
            self.judge_captcha()
        else:
            # TODO. handle error during get page
            QMessageBox.information(self, 'Error', '加载错误。', QMessageBox.Yes)

    def process_first_page_load_success(self, html):
        self.max_page_from_page = self.parse_max_page_num(html)
        self.is_getting_max_page = False
        self.max_page_got = True
        self.start_new_keyword()

    def pause_for_captcha(self):
        self.detailspide.pause()

    def judge_captcha(self, res = True):
        if self.judging_captcha:
            self.judging_captcha = False
            if res is None:
                # captcha in the page, notify the user
                # if no captcha -> has captcha, pause the spider
                if not self.has_captcha:
                    self.detailspide.pause()
                self.has_captcha = True
                QMessageBox.information(self, '验证', '请完成滑动验证。', QMessageBox.Yes)
            else:
                # if has captcha -> no captcha, continue the spider
                if self.has_captcha:
                    self.detailspide.cont()
                self.has_captcha = False
                # no captcha in the page, continue
                scroll_count = 0
                while scroll_count < 10:
                    self.page().runJavaScript("window.scrollBy(0, 1000)")
                    scroll_count += 1
                if self.is_getting_max_page:
                    # toHtml is an ansynchronized method, it will call process_first_page_load_success after it complete
                    self.page().toHtml(self.process_first_page_load_success)
                else:
                    # get page correctly
                    # toHtml is an ansynchronized method, it will call process_search_page_downloaded after it complete
                    self.page().toHtml(self.process_search_page_downloaded)
        else:
            self.judging_captcha = True
            self.page().runJavaScript("document.getElementById('mainsrp-itemlist')", self.judge_captcha)


    def process_search_page_downloaded(self, html):
        # 1' parse url of item detail from page
        urls_list = self.parse_search_result(html)
        # 2' add detail urls to detail spider
        self.detailspide.add_url(urls_list)
        # if detail spider is sleeping, wake it up
        if self.detailspide.sleeping:
            self.detailspide.start_craw()
        # 3' goto next page
        self.current_page += 1
        if self.current_page <= self.max_page:
            # . next page exists
            self.load(QUrl(self.search_base_url.format(quote(self.keywords[self.current_key_words_indx][1]),
                                                       44 * (self.current_page - 1))))
        else:
            # . the last page of the keyword
            print("items url of keywords {} get complete.".format(self.keywords[self.current_key_words_indx]))
            self.current_key_words_indx += 1
            self.start_new_keyword()

    def parse_max_page_num(self, html):
        # TODO. get max page from html
        return 20

    def parse_search_result(self, html):
        # TODO. parse url from search result
        return [
            "http://item.taobao.cm/item.htm?id=567151428614&ns=1&abbucket=2#detail",
            "http://item.taobao.com/item.htm?id=562435302276&ns=1&abbucket=2#detail",
            "http://detail.tmall.com/item.htm?id=569050221976&ns=1&abbucket=2",
            "http://item.taobao.com/item.htm?id=564947907750&ns=1&abbucket=2#detail"
        ]
    def get_max_page_of_current_indx(self):
        self.is_getting_max_page = True
        return 20

    def start_new_keyword(self):
        if not self.max_page_got:
            if self.current_key_words_indx < self.MAX_KEY_WORD_INDX:
                self.current_page = self.keywords[self.current_key_words_indx][0]
                self.is_getting_max_page = True
                self.load(QUrl(self.search_base_url.format(quote(self.keywords[self.current_key_words_indx][1]), 0)))
            else:
                print("All keywords get complete.")
        else:
            self.max_page_got = False
            self.max_page = min(self.LIMIT_PAGE_INDX, self.keywords[self.current_key_words_indx][2], self.max_page_from_page)
            if self.current_page <= self.max_page:
                self.load(QUrl(self.search_base_url.format(quote(self.keywords[self.current_key_words_indx][1]), 44 * (self.current_page - 1))))
            else:
                print("items url of keywords {} get complete.".format(self.keywords[self.current_key_words_indx]))
                self.current_key_words_indx += 1
                self.start_new_keyword()


    def start_craw(self):
        self.start_new_keyword()

if __name__ == '__main__':
    app = QApplication([])
    detail_spider = SaveAsSpider()
    search_spider = SearchSpider(detail_spider)
    search_spider.start_craw()
    search_spider.show()
    detail_spider.start_craw()
    detail_spider.show()
    app.exec()
