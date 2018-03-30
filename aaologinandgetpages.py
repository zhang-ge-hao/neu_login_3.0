# This Python file uses the following encoding: utf-8
import json
import re
import traceback
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import Select
from pyvirtualdisplay import Display
from bs4 import BeautifulSoup
from getverificationcode import *


aao_url = 'https://zhjw.neu.edu.cn/'

login_success_message = 'Login successed.'
verification_code_fail_message = 'Verification code recognition failed.'
login_fail_message = 'Login failed.'
exception_fail_message = 'An exception occurred in the program : '
parameters_miss_fail_message = 'Missing some parameters.'


class DriverMode:
    CHROME = 1
    HEADLESS = 2
    DISPLAY = 4


suitable_mode = DriverMode.CHROME | DriverMode.HEADLESS


def input_login_message_at_aao_page(student_id, password, agnomen, driver):
    input_text = driver.find_element_by_id('WebUserNO')
    input_text.send_keys(student_id)
    input_text = driver.find_element_by_id('Password')
    input_text.send_keys(password)
    input_text = driver.find_element_by_id('Agnomen')
    input_text.send_keys(eval(agnomen))
    input_text.submit()


def get_class_list(page_source):
    res_dict = {'key': '', 'value': {'cols_title': [], 'rows_title': [], 'items': []}}
    soup = BeautifulSoup(page_source, "html5lib")
    tds = soup.find_all('td')
    cols = []
    rows = []
    items = []
    for td in tds:
        if td.has_attr('class') and 'color-header' in td['class']:
            col_row_str = str(td.text).replace("\xa0", "").replace(" ", "")
            if col_row_str != "":
                if len(cols) == 7:
                    rows.append(col_row_str)
                else:
                    if res_dict['key'] == '':
                        res_dict['key'] = col_row_str
                    else:
                        cols.append(col_row_str)
        elif len(cols) == 7 and len(items) < 42:
            td_str = str(td)
            td_str = re.search("(?<=>).*(?=</td>)", td_str).group()
            td_str = re.sub("<br.*?>", "|", td_str)
            items.append(td_str.replace("\xa0", "").replace(u'\u00a0', ''))
    res_dict['value']['rows_title'] = rows
    res_dict['value']['cols_title'] = cols
    for i in range(len(items)):
        if items[i] != '':
            day_con = i % 7
            time_con = int(i / 7)
            res_dict['value']['items'].append\
                ({'col': day_con, 'row': time_con, 'value': items[i]})
    return res_dict


def get_score_list(page_source):
    res_dict = {'key': '', 'value': {'cols_title': [], 'items': []}}
    cols = []
    items = []
    soup = BeautifulSoup(page_source, "html5lib")
    tds = soup.find_all('td')
    for td in tds:
        for br in td.find_all('brs'):
            br.decompose()
        if td.has_attr('class') and 'color-header' in td['class']:
            cols.append(td.text)
        else:
            if len(cols) == 11:
                if re.match("共有记录数[0-9]*", td.text):
                    break
                else:
                    items.append(td.text.replace('\xa0', ''))
    res_dict['value']['cols_title'] = cols
    for i in range(len(items)):
        if items[i] != '':
            res_dict['value']['items'].append({'col': i % 11, 'value': items[i]})
    return res_dict


def get_message_on_page1(driver, res):
    driver.get(aao_url+'ACTIONFINDSTUDENTINFO.APPPROCESS?mode=1')
    soup = BeautifulSoup(driver.page_source, "html5lib")
    title = None
    tds = soup.find_all('td')
    # print(tds)
    for td in tds:
        spans = td.find_all('span')
        if len(spans) == 1 and spans[0].has_attr('class') and 'style3' in spans[0]['class']:
            title = spans[0].string
        elif title is not None:
            value = td.string.replace(u'\u00a0',u"")
            title = title.replace(u'\u00a0', u"")
            res.append({'key': title, 'value': value})
            title = None


def get_message_on_page2(driver, res):
    driver.get(aao_url + 'ACTIONQUERYSTUDENTSCHEDULEBYSELF.APPPROCESS')
    soup = BeautifulSoup(driver.page_source, "html5lib")
    options = soup.find_all('option')
    for i in range(len(options)):
        select = Select(driver.find_element_by_xpath
                        ("/html/body/table/tbody/tr[2]"
                         "/td/table/tbody/tr[1]/td/table/tbody/tr/td[2]/select"))
        select.select_by_index(i)
        driver.find_element_by_xpath\
            ("/html/body/table/tbody/tr[2]"
             "/td/table/tbody/tr[1]/td/table"
             "/tbody/tr/td[3]/input").click()
        res.append(get_class_list(driver.page_source))


def get_message_on_page3(driver, res):
    driver.get(aao_url + 'ACTIONQUERYSTUDENTSCORE.APPPROCESS')
    soup = BeautifulSoup(driver.page_source, "html5lib")
    options = soup.find_all('option')
    tds = soup.find_all('td')
    content = tds[3].text
    content = re.search("(?<=平均学分绩点：)[0-9.]*", content).group()
    res.append({'key': '平均学分绩点', 'value': float(content)})
    for i in range(len(options)):
        select = Select(driver.find_element_by_xpath
                        ("/html/body/table/tbody/tr[2]"
                         "/td/form/table/tbody/tr[1]/td"
                         "/table/tbody/tr/td[2]/select"))
        select.select_by_index(i)
        driver.find_element_by_xpath \
            ("/html/body/table/tbody/tr[2]/td/form/table"
             "/tbody/tr[1]/td/table/tbody/tr/td[3]/input").click()
        page_item = get_score_list(driver.page_source)
        page_item['key'] = options[i].string
        res.append(page_item)


def get_message_on_pages(driver):
    res = []
    get_message_on_page1(driver, res)
    get_message_on_page3(driver, res)
    get_message_on_page2(driver, res)
    return res


def login_and_get_pages(student_id, password, mode=0):
    res = {'information': [], 'pages_message': []}
    display = None
    if mode & DriverMode.DISPLAY != 0:
        display = Display(visible=0, size=(1000, 1000))
        display.start()
    options = Options()
    if mode & DriverMode.HEADLESS != 0:
        options.add_argument('--headless')
    if mode & DriverMode.CHROME != 0:
        driver = webdriver.Chrome(chrome_options=options)
    else:
        driver = webdriver.Firefox()
    driver.get(aao_url)
    verification_code = get_verification_code_from_driver(driver)
    # print(verification_code)
    if re.search(r'^[0-9][+*][0-9]$', verification_code) is None:
        res['information'].append(verification_code_fail_message)
        return res
    input_login_message_at_aao_page\
        (student_id, password, verification_code, driver)
    while ec.alert_is_present()(driver):
        alert_ele = driver.switch_to.alert
        res['information'].append(alert_ele.text)
        alert_ele.accept()
    # print(driver.title)
    time.sleep(1)
    if driver.title != '网络综合平台':
        res['information'].append(login_fail_message)
    else:
        res['pages_message'] = get_message_on_pages(driver)
        res['information'].append(login_success_message)
    driver.quit()
    if display is not None:
        display.stop()
    return res


def login_and_get_pages_api(request_json_str):
    try:
        request = json.loads(request_json_str)
        if 'student_id' in request and 'password' in request:
            student_id = request['student_id']
            password = request['password']
            res = json.dumps(login_and_get_pages(student_id, password, suitable_mode))
        else:
            res = '{"information":["'+parameters_miss_fail_message+'"],"pages_message":[]}'
    except BaseException as e:
        traceback.print_exc()
        res = '{"information":["'+exception_fail_message+str(e)+'"],"pages_message":[]}'
    return res.encode('utf-8').decode('unicode_escape')

'''
json_str = json.dumps({'student_id': '',
                      'password': ''})
print(login_and_get_pages_api(json_str))
'''
