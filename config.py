#!/usr/bin/env python3
# coding=utf-8

config = {
    "SAVE_DIR":"/tmp/savepages/detail_pages",
    "URL_LIST_FILE":"/tmp/savepages/detail_url_list",
    "START_URL_INDX":0,
    "URL_LIST_WRITE_BACK_FILE":"/tmp/savepages/detail_url_list_write_back",
    'KEY_WORDS':[(1, '小米', 20), (1, 'oppo', 20), (1, 'vivo', 20), (1, '真维斯', 20)],
    'START_KEYWORD': 0,
    'MAX_PAGE': 50,
    'SEARCH_BASE_URL':'https://s.taobao.com/search?q={0}&s={1}'
}
js = {
    "search_keyword":'''
        function search(keyword){
            query_input = document.getElementById("q")
            query_input.value = keyword
            btn_search = document.getElementsByClassName("btn-search tb-bg")
            if(btn_search.length > 0){
                btn_search = btn_search[0]
                btn_search.click()
                return true
            }
            else {
                return false
            }
        }
        search({0})
    ''',
    "judge_captcha":'document.getElementById("nc_1__scale_text")'
}