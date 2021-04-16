import datetime
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait


class SchuManDriver:
    def __init__(self, headless=True):
        wd_options = webdriver.FirefoxOptions()
        wd_options.headless = headless

        self.driver = webdriver.Firefox(options=wd_options)

    def logout(self):
        wait = WebDriverWait(self.driver, 10)
        self.driver.get("https://login.schulmanager-online.de/#/dashboard")
        wait.until(expected_conditions.presence_of_element_located(
            (By.XPATH, '/html/body/div[2]/navbar/div/div/div[4]/ul[1]/li[5]/a'))).click()

        wait.until(expected_conditions.alert_is_present())
        alert = self.driver.switch_to.alert
        alert.accept()

    def login(self, username, password):
        # get website
        self.driver.get("https://login.schulmanager-online.de")

        wait = WebDriverWait(self.driver, 10)
        # wait for email field and enter login
        wait.until(expected_conditions.presence_of_element_located((By.XPATH, '//*[@id="emailOrUsername"]'))) \
            .send_keys(username)
        # wait for password field and enter login
        wait.until(expected_conditions.presence_of_element_located((By.XPATH, '//*[@id="password"]'))) \
            .send_keys(password)
        # wait for submit button and click it
        wait.until(expected_conditions.presence_of_element_located((
            By.XPATH, '/html/body/div[2]/div/div/div[2]/div[3]/div[2]/div/form/div[5]/span/button'))) \
            .click()
        while True:
            if self.driver.current_url != "https://login.schulmanager-online.de/#/login":
                return 0
            elif len(self.driver.find_elements_by_xpath('/html/body/div[2]/div/div/div[2]/div[3]/div[2]/div/form/div[3][@class="alert alert-danger"]')) != 0:
                return 1
                # TODO timeout, sleep

    def get_videoconferences(self):
        wait = WebDriverWait(self.driver, 10)
        # go to video conference screen
        self.driver.get(
            'https://login.schulmanager-online.de/#/modules/video/meetings')
        # locate video conference list
        vc_container = wait.until(expected_conditions.presence_of_element_located(
            (By.XPATH, '/html/body/div[2]/div/ui-view/ui-view/div[2]/div/div[1]/div[2]/table/tbody')))
        # find list elements
        vc_list = vc_container.find_elements_by_xpath('tr')

        result = []
        for vc in vc_list:
            # extract time and title from text
            raw_vc_time = vc.find_element_by_xpath('td[1]').text
            vc_title = vc.find_element_by_xpath('td[2]').text
            # parse time to datetime.datetime object
            match = re.match(
                r'^((\d\d)\.(\d\d))\., ((\d\d):(\d\d)) - \d\d:\d\d Uhr$', raw_vc_time)
            vc_time = datetime.datetime(
                datetime.datetime.now().year,
                int(match.group(3)),
                int(match.group(2)),
                int(match.group(5)),
                int(match.group(6))
            )

            result.append((vc_time, vc_title))
        return result

    def get_subjects(self):
        wait = WebDriverWait(self.driver, 10)

        self.driver.get(
            'https://login.schulmanager-online.de/#/modules/learning/student//select-course')

        subject_container = wait.until(expected_conditions.presence_of_element_located(
            (By.XPATH, '/html/body/div[2]/div/ui-view/ui-view/ui-view/div[1]/div[2]')))
        subject_list = subject_container.find_elements_by_xpath(
            'div/table/tbody/tr/td')

        return {int(s.get_attribute('href').split('/')[-1]): s.text for s in subject_list}

    def get_units(self, identifier):
        wait = WebDriverWait(self.driver, 10)
        self.driver.get(
            f'https://login.schulmanager-online.de/#/modules/learning/student//course/{identifier}')

        units_container = wait.until(expected_conditions.presence_of_element_located(
            (By.XPATH, '/html/body/div[2]/div/ui-view/ui-view/ui-view/ui-view/div[2]/div')))

        results = []

        for unit in units_container.find_elements_by_xpath('a'):
            identifier = int(unit.get_attribute('href').split('/')[-1])
            done = 'done' in unit.get_attribute('class')
            title = unit.find_element_by_xpath(
                'div[@class="name ng-binding"]').text
            #date = unit.find_element_by_xpath(
            #    'div[@class="date"]/span[@class="d-none d-md-inline ng-binding"]').text

            results.append((identifier, title, done))
        self.driver.get("about:blank")
        return results

    def get_unit(self, subject, unit):
        wait = WebDriverWait(self.driver, 10)
        self.driver.get(
            f"https://login.schulmanager-online.de/#/modules/learning/student//course/{subject}/unit/{unit}")

        unit_texts = wait.until(expected_conditions.presence_of_all_elements_located(
            (By.XPATH, '/html/body/div[2]/div/ui-view/ui-view/ui-view/ui-view/div/div/div/div[2]/view-unit-item')))

        return '\n'.join([unit_text.text for unit_text in unit_texts])
        # /html/body/div[2]/div/ui-view/ui-view/ui-view/ui-view/div/div/div/div[2]/view-unit-item

    # TODO
    # - get unit
    # - get schedule
    # - vconf join?
    # - messages?


if __name__ == '__main__':
    import json

    with open('login.json') as f:
        login = json.load(f)
    driver = SchuManDriver(True)
    driver.login(login['email'], login['password'])
    subjects = driver.get_subjects()
    print(subjects)
    print(driver.get_units(list(subjects)[9]))
    driver.driver.quit()
