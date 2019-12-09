# -*- coding: utf-8 -*-
"""
Created on Tue Nov 19 10:55:09 2019

@author: DavidMeyer
"""
def scrape(query, lang):
    import ipywidgets as widgets
    import os
    import json
    from jinja2 import Environment, FileSystemLoader
    from gquestions import initBrowser, crawlQuestions, newSearch, prettyOutputName, flatten_csv
    from IPython.core.display import display, HTML
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
            filepath = os.path.join('..','files','html', prettyOutputName(query = query))
            with open(filename, 'w') as fh:
                fh.write(template.render(
                        treeData = treeData,
                        ))
                
            display(HTML('<form method="get" action="'+ filepath +'"><br><button class="btn btn-primary" type="submit">Download HTML!</button></form>'))
    browser.close()