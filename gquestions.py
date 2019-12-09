import re
import time
import datetime
import platform
from tqdm import tqdm 
from time import sleep
import pandas as pd
from pandas.io.json import json_normalize
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

''' 
Visualisierung eines Ladebalkens
'''
def sleepBar(seconds):
    for i in tqdm(range(seconds)):
        sleep(1)

def prettyOutputName(query,filetype = 'html'):
    _query = re.sub('\s|\"|\/|\:|\.','_', query.rstrip())
    prettyname = _query
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%d-%m-%Y_%H-%M-%S-%f')
    if filetype != 'html':
        prettyname += "_" + st + "." + filetype
    else:
        prettyname += "_" + st + "." + filetype
    return prettyname


def initBrowser(headless=False):
    if "Windows" in platform.system():
        chrome_path = "driver/chromedriver.exe"
        chrome_options = Options()
    else:
        import os
        os.chmod('/home/jovyan/driver/chromedriver', 755)
        chrome_path = "driver/chromedriver"
        chrome_options = Options()
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-features=NetworkService")
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
    return webdriver.Chrome(options=chrome_options,executable_path=chrome_path)
"""
Search on Google and returns the list of PAA questions in SERP.
"""
def newSearch(browser,query,lang):
    if lang== "de":
        browser.get("https://www.google.com?hl=de")
        searchbox = browser.find_element_by_xpath("//input[@aria-label='Suche']")
    if lang== "en":
        browser.get("https://www.google.com?hl=en")
        searchbox = browser.find_element_by_xpath("//input[@aria-label='Search']")
    else:
        browser.get("https://www.google.com?hl=de")
        searchbox = browser.find_element_by_xpath("//input[@aria-label='Suche']")
    
    searchbox.send_keys(query)
    sleepBar(2)
    tabNTimes(browser)
    if lang== "de":
        searchbtn = browser.find_elements_by_xpath("//input[@aria-label='Google-Suche']")
    if lang== "en":
        searchbtn = browser.find_elements_by_xpath("//input[@aria-label='Google Search']")
    else:
    	searchbtn = browser.find_elements_by_xpath("//input[@aria-label='Google-Suche']")
    try:
        searchbtn[-1].click()
    except:
        searchbtn[0].click()
    sleepBar(2)
    paa = browser.find_elements_by_xpath("//span/following-sibling::div[contains(@class,'match-mod-horizontal-padding')]")
    hideGBar()
    return paa
"""
Helper function that scroll into view the PAA questions element.
"""
def scrollToFeedback(lang, browser):
    if lang == "de":
        el = browser.find_element_by_xpath("//div[@class='kno-ftr']//div/following-sibling::a[text()='Feedback geben']")
    if lang == "en":
        el = browser.find_element_by_xpath("//div[@class='kno-ftr']//div/following-sibling::a[text()='Feedback']")
    else:
    	el = browser.find_element_by_xpath("//div[@class='kno-ftr']//div/following-sibling::a[text()='Feedback geben']")

    actions = ActionChains(browser)
    actions.move_to_element(el).perform()
    browser.execute_script("arguments[0].scrollIntoView();", el)
    actions.send_keys(Keys.PAGE_UP).perform()
    sleepBar(1)
"""
Accessibility helper: press TAB N times (default 2)
"""
def tabNTimes(browser, N=2):
    actions = ActionChains(browser) 
    for _ in range(N):
        actions = actions.send_keys(Keys.TAB)
    actions.perform()

"""
Click on questions N times
"""
def clickNTimes(lang,browser,el, n=1):
    for i in range(n):
        el.click()
        logging.info(f"clicking on ... {el.text}")
        sleepBar(1)
        scrollToFeedback(lang, browser)
        try:
            el.find_element_by_xpath("//*[@aria-expanded='true']").click()
        except:
            pass
        sleepBar(1)

"""
Hide Google Bar to prevent ClickInterceptionError
"""
def hideGBar():
	try:
		browser.execute_script('document.getElementById("searchform").style.display = "none";')
	except:
		pass

"""
Where the magic happens
"""
def crawlQuestions(lang,query,browser,start_paa, paa_list, initialSet):
    depth=0
    _tmp = createNode(paa_lst=paa_list, name=query, children=True)
    
    outer_cnt = 0
    for q in start_paa:
        scrollToFeedback(lang, browser)
        if "Dictionary" in q.text:
            continue
        test = createNode(paa_lst=paa_list, n=0,
                        name=q.text,
                        parent=paa_list[0]["name"],
                        children=True)
        
        clickNTimes(lang,browser,q)
        new_q = showNewQuestions(browser,initialSet)
        for l, value in new_q.items():
            sleepBar(1)
            logging.info(f"{l}, {value.text}")
            test1 = createNode(paa_lst=test[0]["children"][outer_cnt]["children"], 
                                name=value.text,
                                parent=test[0]["children"][outer_cnt]["name"],
                                children=True)
            
        initialSet = getCurrentSERP(browser, browser)
        logging.info(f"Current count: {outer_cnt}")
        outer_cnt += 1
        if depth==1:
            for i in range(depth):
                currentQuestions = []
                for i in initialSet.values():
                    currentQuestions.append(i.text)
                for i in paa_list[0]["children"]:
                    for j in i["children"]:
                        parent = j['name']
                        logging.info(parent)
                        _tmpset = set()
                        if parent in currentQuestions:
                            try:
                                if "'" in parent:
                                    xpath_compiler = '//div[text()="' + parent + '"]'
                                else: 
                                    xpath_compiler= "//div[text()='" + parent + "']"
                                question= browser.find_element_by_xpath(xpath_compiler)
                            except NoSuchElementException:
                                continue
                            scrollToFeedback(lang, browser)
                            sleepBar(1)
                            clickNTimes(lang,browser,question)
                            new_q = showNewQuestions(browser,initialSet)
                            for l, value in new_q.items():
                                if value.text == parent:
                                    continue
                                j['children'].append({"name": value.text,"parent": parent})
                                
                            initialSet = getCurrentSERP(browser, browser)
   
    _path = 'csv/'+prettyOutputName("",'csv')
    flatten_csv(paa_list, depth, _path)
    from IPython.core.display import display, HTML
    display(HTML('<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" crossorigin="anonymous"><form method="get" action="'+ _path +'"><br><button class="btn btn-primary" type="submit">Download CSV!</button></form>'))
"""
Get the current Result Page.
Returns: 
    A list with newest questions.
"""
def getCurrentSERP(browser, browser1):
    _tmpset = {}
    new_paa = browser.find_elements_by_xpath("//span/following-sibling::div[contains(@class,'match-mod-horizontal-padding')]")
    cnt= 0
    for q in new_paa:
        _tmpset.update({cnt:q})
        cnt +=1
    newInitialSet = _tmpset
    return newInitialSet

"""
Shows new questions.
Args:
    intialSet (dict): The initial set in the PAA box.
Returns:
    list of questions with first 3-4 questions deleted (initalSet).
"""
def showNewQuestions(browser,initialSet):
    tmp = getCurrentSERP(browser, browser)
    deletelist = [k for k, v in initialSet.items() if k in tmp and tmp[k] == v]
    _tst = dict.copy(tmp)
    for i,value in tmp.items():
        if i in deletelist:
            _tst.pop(i)
    return _tst

"""
Create a new node in the list.
Args:
    paa_list_elements: list of web elements
    n: index of 'children' list on a main node
    name: node nome
    parent: Indicates if the node has a parent. Default to null only for first level.
    chilren: Indicates if the node has a children list. default false
Returns:
    list of questions with the current new node
"""
def createNode( n=-1, parent='null', children=False, name='',*, paa_lst):
    logging.info(paa_lst)
    if children:
        _d = {
        "name": name,
        "parent": parent,
        "children": [] 
        }
    else:
        _d = {
        "name": name,
        "parent": parent
        }
    if n!=-1:
        logging.info(paa_lst[n]["children"])
        paa_lst[n]["children"].append(_d)
    else:
        paa_lst.append(_d)
    

    return paa_lst

"""
This func takes in input JSON data and returns csv file.
"""
def flatten_csv(data,depth,prettyname):
    try:
        if depth == 0:
            _ = json_normalize(data[0]["children"], 'children', ['name', 'parent',['children',]], record_prefix='inner.')
            _.drop(columns=['children','inner.children','inner.parent'], inplace=True)
            columnTitle = ['parent','name','inner.name']
            _ = _.reindex(columns=columnTitle)
            _.to_csv(prettyname,sep=";",encoding='utf-8')
        elif depth == 1:
            df = json_normalize(data[0]["children"], meta=['name','children','parent'], record_path="children", record_prefix='inner.')
            frames = [ json_normalize(i) for i in df['inner.children'] ]
            result = pd.concat(frames)
            result.rename(columns={"name": "inner.inner.name", "parent": "inner.name"}, inplace=True)
            merge = pd.merge(df, result, how='left', on="inner.name")
            merge.drop(columns=['name'], inplace=True)
            columnTitle = ['parent','inner.parent','inner.name','inner.inner.name']
            merge = merge.reindex(columns=columnTitle)
            merge = merge.drop_duplicates(subset='inner.inner.name', keep='first')
            merge.to_csv(prettyname,sep=';',encoding='utf-8')
    except Exception as e:
        logging.warning(f"{e}")