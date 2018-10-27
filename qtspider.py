#!/usr/bin/env python3
# coding=utf-8

from PyQt5.QtCore import QObject, QTimer
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineDownloadItem
from PyQt5.QtCore import QUrl
from config import config as cfg
from urllib.parse import parse_qs, urlparse
import time
import random
import os

# class MyTimer(QTimer):
#     def __init__(self, spider):
#         self.spider = spider
#         self.timeout.connect(self.process_timeout)
#
#     def process_timeout(self):
#         if self.spider.is_downloading:
#             self.start(2000)
#         else:
#             spider.goto_next_page()


class SaveAsSpider(QWebEngineView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loadFinished.connect(self.process_load_finished)
        self.page().profile().downloadRequested.connect(self.process_download_request)
        self.url_list = self.read_save_url_list(cfg['URL_LIST_FILE'])
        self.current_url_indx = cfg['START_URL_INDX']
        self.MAX_URL_INDX = len(self.url_list)
        self.SAVE_DIR = cfg['SAVE_DIR']
        self.is_downloading = False
        if not os.path.exists(self.SAVE_DIR):
            os.mkdir(self.SAVE_DIR)
        # self.timer = MyTimer(self)

    def process_download_finished(self):
        self.is_downloading = False
        print("downloading finished.")

    def process_timer_finished(self):
        if self.is_downloading:
            QTimer.singleShot(2000, self.process_timer_finished)
        else:
            self.goto_next_page()


    def process_load_finished(self, status):
        # 1. slide down to load full page
        scroll_count = 0
        while scroll_count < 10:
            self.page().runJavaScript("window.scrollBy(0, 1000)")
            self.show()
            # time.sleep(random.randint(1, 3))
            time.sleep(0.5)
            scroll_count += 1
        # 2. save page as complete mhtml file
        # this can save page as a mhtml file which contains the web file and resource file
        self.is_downloading = True
        self.page().save(os.path.join(self.SAVE_DIR, self.url_list[self.current_url_indx][0] + ".mhtml"), format=QWebEngineDownloadItem.MimeHtmlSaveFormat)
        # this can save page as a html file and a directory with resources
        # self.page().save(os.path.join(self.SAVE_DIR, self.url_list[self.current_url_indx][0] + ".html"), format=QWebEngineDownloadItem.CompleteHtmlSaveFormat)
        # self.page().download(QUrl(self.url_list[self.current_url_indx][1]), os.path.join(self.SAVE_DIR, self.url_list[self.current_url_indx][0] + ".html"))
        QTimer.singleShot(2000, self.process_timer_finished)

    def goto_next_page(self):
        # 3. load next url into page
        self.current_url_indx += 1
        if self.current_url_indx < self.MAX_URL_INDX:
            self.load(QUrl(self.url_list[self.current_url_indx][1]))
        else:
            print("detail page save success")



    def process_download_request(self, item):
        item.finished.connect(self.process_download_finished)
        print("save {} to {}".format(item.url(), item.path()))
        item.accept()

    def read_save_url_list(self, filename):
        res = []
        with open(filename) as f:
            for line in f:
                # parse id from url as the save filename
                id = parse_qs(urlparse(line).query).get('id', None)
                if id is not None:
                    res.append((id[0], line))
        return res

    def start_craw(self):
        if self.current_url_indx < self.MAX_URL_INDX:
            self.load(QUrl(self.url_list[self.current_url_indx][1]))
        else :
            print('START_URL_INDX > number of urls')

DetailSpider = SaveAsSpider

class SearchSpider(QWebEngineView):
    def __init__(self):
        pass

    def process_load_finished(self):
        pass

    def parse_search_result(self):
        pass


if __name__ == '__main__':
    app = QApplication([])
    spider = SaveAsSpider()
    spider.start_craw()
    spider.show()
    app.exec()
