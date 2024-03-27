from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
import time
import json
import requests

def sendTelegramMessage(message):
    user_id = 'your_user_id'
    bot_token = 'your_bot_token'
    # bot = Bot(token = botToken)
    # bot.send_message(chat_id=chatId, text=message)
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={user_id}&text={message}"
    requests.get(url).json()  # this sends the message

# read from json
with open('config.json', encoding='utf-8') as f:
    data = json.load(f)
    user_nereden = data['nereden']
    user_nereye = data['nereye']
    user_tarih = data['tarih']
    user_hour = data['saat']
    states = [-1 for _ in user_hour]
    timeout = int(data['timeout'])


def initial_search():
    # Open the browser and go to the website
    options = Options()
    # user agent
    # Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    options.add_argument('--log-level=3')
    options.add_argument('--disable-logging')
    options.add_argument('--no-sandbox')
    options.add_argument('--headless=new')
    options.headless = True
    options.add_argument('--disable-gpu')

    options.page_load_strategy = 'normal'
    
    browser = webdriver.Chrome(options=options)
    browser.get('https://ebilet.tcddtasimacilik.gov.tr/view/eybis/tnmGenel/tcddWebContent.jsf')

    # nereden
    browser.find_element(By.XPATH, '//*[@id="nereden"]').send_keys(user_nereden)
    time.sleep(1)
    ActionChains(browser).send_keys(Keys.DOWN).send_keys(Keys.RETURN).perform()
    time.sleep(1)

    # nereye
    browser.find_element(By.XPATH, '//*[@id="nereye"]').send_keys(user_nereye)
    time.sleep(1)
    ActionChains(browser).send_keys(Keys.DOWN).send_keys(Keys.RETURN).perform()
    time.sleep(1)

    # tarih
    tarih = browser.find_element(By.XPATH, '//*[@id="trCalGid_input"]')
    tarih.clear()
    time.sleep(1)
    tarih.send_keys(user_tarih)
    ActionChains(browser).send_keys(Keys.TAB).perform()
    time.sleep(1)

    # ara
    browser.find_element(By.XPATH, '//*[@id="btnSeferSorgula"]/span').click()

    return browser

def get_browser():
    browser = initial_search()
    while(browser.current_url == 'https://ebilet.tcddtasimacilik.gov.tr/view/eybis/tnmGenel/tcddWebContent.jsf?expired=true'):

        browser.quit()
        time.sleep(1)
        browser = initial_search()
    return browser



def check_yht(counter = 0):
    browser = get_browser()
    # Wait for the page to load
    time.sleep(5)
    # Locate the table element
    table = browser.find_element(By.XPATH, '//*[@id="mainTabView:gidisSeferTablosu_data"]')

    # Get all rows of the table
    rows = table.find_elements(By.TAG_NAME, 'tr')
    while rows == []:
        if counter > 5:
            return
        browser.quit()
        time.sleep(1)
        check_yht(counter + 1)
        return

    for row in rows:
        # Extract data from each cell in the row
        cells = row.find_elements(By.TAG_NAME, 'td')
        hour = cells[0].text.split('\n')[1].strip()

        isYht = (cells[3].text).find('YHT') != -1

        if(isYht and hour in user_hour):
            countInfo = (cells[4].text).split(')')[1].replace('(', '').strip()
            
            try:
                countInfo = int(countInfo)
            except:
                countInfo = 0

            if(countInfo != states[user_hour.index(hour)]):
                states[user_hour.index(hour)] = countInfo
                if(countInfo > 0):
                    sendTelegramMessage(f'{user_nereden} - {user_nereye} arası {user_tarih} {hour} tarihli YHT seferinde {countInfo} kişilik yer bulunmaktadır.')
                else:
                    sendTelegramMessage(f'{user_nereden} - {user_nereye} arası {user_tarih} {hour} tarihli YHT seferinde yer bulunmamaktadır.')
    browser.quit()
    time.sleep(1)

while True:
    try:
        check_yht()
    except Exception as e:
        pass
    time.sleep(timeout)
