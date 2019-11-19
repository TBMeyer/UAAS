# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 10:55:09 2019

@author: DavidMeyer
"""
def scrape(query, lang):
    import ipywidgets as widgets
    import os
    import re
    import sys
    import json
    import time
    import datetime
    import platform
    from docopt import docopt
    from tqdm import tqdm 
    from time import sleep
    import pandas as pd
    from pandas.io.json import json_normalize
    import logging
    from jinja2 import Environment, FileSystemLoader
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
    from gquestions import initBrowser, crawlQuestions, sleepBar, tabNTimes, newSearch, prettyOutputName
    widgets.IntSlider()
    browser = initBrowser()
    start_paa = newSearch(browser,query, lang)
    initialSet = {}
    cnt= 0
    for q in start_paa:
        initialSet.update({cnt:q})
        cnt +=1
    paa_list = []
    crawlQuestions(lang, query,browser,start_paa, paa_list, initialSet)
    treeData = 'var treeData = ' + json.dumps(paa_list) + ';'
    if paa_list[0]['children']:
            root = os.path.dirname(os.path.abspath("gquestions.py"))
            templates_dir = os.path.join(root, 'templates')
            env = Environment( loader = FileSystemLoader(templates_dir) )
            template = env.get_template('index.html')
            filename = os.path.join(root, 'html', prettyOutputName(query = query))
            with open(filename, 'w') as fh:
                fh.write(template.render(
                        treeData = treeData,
                        ))
    browser.close()