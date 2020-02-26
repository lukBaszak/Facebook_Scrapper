import datetime

from selenium.webdriver.support.wait import WebDriverWait

from credentials import *
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium.webdriver import Proxy
from selenium.webdriver.common.proxy import ProxyType
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from multiprocessing import Process

from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem

from time import sleep
import logging

logging.basicConfig(filename='logger.log', level=logging.INFO)


def get_web_driver():
    try:
        software_names = [SoftwareName.FIREFOX.value]
        operating_system = [OperatingSystem.WINDOWS.value,
                            OperatingSystem.LINUX.value]
        user_agent_rotator = UserAgent(software_names=software_names,
                                       operating_system=operating_system,
                                       limit=1000)
        user_agent = user_agent_rotator.get_random_user_agent()

        firefox_options = Options()
        firefox_options.add_argument('--window-size=1520,1080')
        firefox_options.add_argument('--disable-gpu')
        # firefox_options.add_argument('--headless')
        firefox_options.add_argument(f'user-agent={user_agent}')

        browser = webdriver.Firefox(firefox_options=firefox_options,
                                    executable_path=r'geckodriver.exe')

        return browser

    except WebDriverException:
        return "WebDriverException"


def get_desired_group_list(group_list):
    line_list = [line.rstrip('\n') for line in open('key_groups.txt')]
    links_list = []
    for group in group_list:
        group_name = group.find_element_by_tag_name('span').text
        if group_name in line_list:
            links_list.append(group.find_element_by_tag_name('a').get_attribute('href'))
    return links_list


class Request:

    def __init__(self, url):
        self.browser = get_web_driver()
        self.url = url
        self.margin = datetime.timedelta(minutes=15)
        self.current_time = datetime.datetime.now()
        logging.info(str((self.current_time - self.margin).strftime(' %d/%m/%y - %H:%m')) + ' - ' + str(
            self.current_time.strftime('%d/%m/%y - %H:%m')))

    def get_selenium_res(self):
        self.browser.get(self.url)

        try:
            username = self.browser.find_element_by_id('email')
            password = self.browser.find_element_by_id('pass')
            submit = self.browser.find_element_by_id('loginbutton')

            username.send_keys(credential_email)
            password.send_keys(credential_password)

            submit.click()
        except NoSuchElementException:
            return self.get_selenium_res()

        nav_button = self.browser.find_element_by_id('navItem_1434659290104689')
        webdriver.ActionChains(self.browser).move_to_element(nav_button).click(nav_button).perform()
        sleep(2)

        # if there is expand button
        while True:
            try:
                a_ele = self.browser.find_element_by_link_text('See more...')
                # expand group list
                a_ele.find_element_by_tag_name('i').click()
                sleep(0.5)

            except NoSuchElementException:
                break

        group_list = self.browser.find_elements_by_class_name('_2yaa')
        links_list = get_desired_group_list(group_list)
        for link in links_list:
            link = link + '&sorting_setting=CHRONOLOGICAL'
            self.browser.get(link)

            while True:
                # get posts feed
                posts_mall = self.browser.find_element_by_id('pagelet_group_mall')

                posts = posts_mall.find_elements_by_css_selector(
                    "div[class='_4-u2 mbm _4mrt _5jmm _5pat _5v3q _7cqq _4-u8']")

                # get date of creating last visible post
                date = posts[-1].find_element_by_tag_name('abbr').get_attribute('title')
                datetime_object = datetime.datetime.strptime(date, '%d/%m/%Y, %H:%M')

                # if last post is still in range -> load more
                if self.current_time - self.margin <= datetime_object:
                    self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                else:
                    for post in posts:
                        try:

                            date = post.find_element_by_tag_name('abbr').get_attribute('title')
                            datetime_object = datetime.datetime.strptime(date, '%d/%m/%Y, %H:%M')

                            # if post's initial date is within range -> check presence of key words
                            if self.current_time - self.margin <= datetime_object <= self.current_time:

                                lines = post.find_elements_by_tag_name('p')
                                for line in lines:
                                    keywords_list = [line.rstrip('\n') for line in open('keywords.txt')]
                                    for word in keywords_list:
                                        if word in line.text:
                                            direct_link = post.find_element_by_class_name('_5pcq').get_attribute('href')
                                            print('keyword found!')
                                            logging.info(
                                                ' keyword: {} was found in the post: {}'.format(word, direct_link))
                        except NoSuchElementException:
                            pass
                    break

        self.browser.close()


while True:
    request = Request('https://www.facebook.com')
    request.get_selenium_res()

    sleep(900)
