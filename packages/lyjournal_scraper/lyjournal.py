import logging
import os
import pathlib
import shutil
import stat
import time
from typing import Any, Callable, Optional, Union

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    TimeoutException)
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.remote.remote_connection import LOGGER
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from webdriver_manager.firefox import GeckoDriverManager

from .config import Config
from .log import get_logger


class ElementFinder:
    SEARCH_RESULT_ANALYSIS_IMAGE_XPATH: str = \
        '/html/body/form/table/tbody/tr[3]/td/table/tbody/tr/td[1]/table/tbody/tr[1]/td/img'
    NO_RESULT_XPATH: str = '/html/body/form/table/tbody/tr[3]/td/table/tbody/tr[1]/td/font/b/font'

    @classmethod
    def find_search_box(cls, element: WebDriver | WebElement) -> Optional[WebElement]:
        try:
            return element.find_element(
                By.XPATH,
                '/html/body/form/table/tbody/tr[3]/td/table/tbody/tr[2]/'
                'td/table/tbody/tr[1]/td/table/tbody/tr/td[3]/input[2]')
        except NoSuchElementException:
            return

    @classmethod
    def find_search_button(cls, element: WebDriver | WebElement) -> Optional[WebElement]:
        try:
            return element.find_element(
                By.XPATH,
                '/html/body/form/table/tbody/tr[3]/td/table/tbody/tr[2]/'
                'td/table/tbody/tr[1]/td/table/tbody/tr/td[4]/input')
        except NoSuchElementException:
            return

    @classmethod
    def find_no_such_result_text(cls, element: WebDriver | WebElement) -> Optional[WebElement]:
        try:
            return element.find_element(By.XPATH, cls.NO_RESULT_XPATH)
        except NoSuchElementException:
            return

    @classmethod
    def find_search_result_analysis_image(cls, element: WebDriver | WebElement) -> Optional[WebElement]:
        try:
            return element.find_element(By.XPATH, cls.SEARCH_RESULT_ANALYSIS_IMAGE_XPATH)
        except NoSuchElementException:
            return

    @classmethod
    def find_search_result_link(cls, element: WebDriver | WebElement, row_idx: int) -> Optional[WebElement]:
        try:
            return element.find_element(
                By.XPATH,
                '/html/body/form/table/tbody/tr[3]/td/table/tbody/tr/td[2]/table/'
                f'tbody/tr[2]/td/table/tbody/tr[2]/td/table/tbody/tr[{row_idx}]/td[4]/a')
        except NoSuchElementException:
            return

    @classmethod
    def find_search_result_links(cls, element: WebDriver | WebElement) -> list[WebElement]:
        res: list[WebElement] = list()
        for i in range(1, 12):
            link: Optional[WebElement] = cls.find_search_result_link(element, i)
            if link:
                res.append(link)
        return res

    @classmethod
    def find_next_page_button(cls, element: WebDriver | WebElement) -> Optional[WebElement]:
        try:
            return element.find_element(
                By.XPATH,
                '/html/body/form/table/tbody/tr[3]/td/table/tbody/tr/td[2]/table/tbody/tr[1]/td/'
                'table/tbody/tr[3]/td/table/tbody/tr/td[2]/table/tbody/tr/td[4]/input')
        except NoSuchElementException:
            return

    @classmethod
    def find_result_detail_image(cls, element: WebDriver | WebElement) -> Optional[WebElement]:
        try:
            return element.find_element(By.XPATH, '/html/body/form/table/tbody/tr[3]/td/table/tbody/tr[1]/td/img')
        except NoSuchElementException:
            return

    @classmethod
    def find_result_detail_table(cls, element: WebDriver | WebElement) -> Optional[WebElement]:
        try:
            return element.find_element(By.XPATH, '/html/body/form/table/tbody/tr[3]/td/table/tbody/tr[2]/td/table')
        except NoSuchElementException:
            return


class SimpleLYJournal:
    HOME_PAGE: str = "https://lis.ly.gov.tw/qrkmc/qrkmout"

    def __init__(self, config: Config) -> None:
        self.cache_path: pathlib.Path = pathlib.Path("cache").absolute()
        self.config: Config = config

        self.clear_cache()

        LOGGER.setLevel(logging.WARNING)

        self.browser_driver: WebDriver
        if config.browser.lower() == 'firefox':
            self.browser_driver = webdriver.Firefox(
                service=Service(GeckoDriverManager().install()))
        else:
            edge_options: webdriver.EdgeOptions = webdriver.EdgeOptions()
            edge_options.add_argument(f"user-data-dir={self.cache_path}")
            self.browser_driver = webdriver.Edge(
                EdgeChromiumDriverManager().install(), options=edge_options)

    def clear_cache(self) -> None:
        def on_rm_error(func: Callable[[Any], None], path: str, exc_info: Any):
            os.chmod(path, stat.S_IWRITE)
            func(path)
        if self.cache_path.is_dir():
            shutil.rmtree(self.cache_path, onerror=on_rm_error)
        if not self.cache_path.is_dir():
            self.cache_path.mkdir()

    def get_metas_from_search_result_link(self, link: str) -> dict[str, str]:
        meta: dict[str, str] = dict()
        e: Optional[Union[ElementClickInterceptedException, TimeoutException]] = None
        search_window: str = self.browser_driver.current_window_handle

        i: int
        for i in range(100):
            try:
                self.browser_driver.execute_script('window.open()')
                d: webdriver.Edge | webdriver.Firefox
                WebDriverWait(self.browser_driver, 10).until(lambda d: len(d.window_handles) > 1)
                self.browser_driver.switch_to.window(
                    self.browser_driver.window_handles[len(self.browser_driver.window_handles) - 1])
                self.browser_driver.get(link)
                WebDriverWait(self.browser_driver, 10).until(
                    lambda d: ElementFinder.find_result_detail_image(d))
            except (ElementClickInterceptedException, TimeoutException) as e:
                get_logger().info(f"retry: {i+1}")
                while len(self.browser_driver.window_handles) > 1:
                    self.browser_driver.switch_to.window(
                        self.browser_driver.window_handles[len(self.browser_driver.window_handles) - 1])
                    self.browser_driver.close()
                self.browser_driver.switch_to.window(search_window)
                time.sleep(1)
                continue
            else:
                break
        else:
            if e:
                raise e

        data_table: WebElement = ElementFinder.find_result_detail_table(self.browser_driver)
        field: WebElement
        value: WebElement
        meta: dict[str, str] = {"連結": self.browser_driver.current_url}
        for field, value in zip(
                data_table.find_elements(By.CLASS_NAME, 'dettb01'),
                data_table.find_elements(By.CLASS_NAME, 'dettb02')):
            if not field.text.strip():
                continue
            meta[field.text.strip()] = value.text.strip()

        self.browser_driver.close()
        self.browser_driver.switch_to.window(search_window)
        return meta

    def search(self, keyword: str) -> list[dict[str, str]]:
        results: list[dict[str, str]] = list()
        e: Optional[TimeoutException] = None

        i: int
        for i in range(100):
            try:
                self.browser_driver.get(self.HOME_PAGE)
                d: webdriver.Edge | webdriver.Firefox

                WebDriverWait(self.browser_driver, 10).until(lambda d: ElementFinder.find_search_box(d))
                WebDriverWait(self.browser_driver, 10).until(lambda d: ElementFinder.find_search_button(d))

                ElementFinder.find_search_box(self.browser_driver).clear()
                ElementFinder.find_search_box(self.browser_driver).send_keys(keyword)
                ElementFinder.find_search_button(self.browser_driver).click()

                WebDriverWait(self.browser_driver, 10).until(
                    lambda d: ElementFinder.find_no_such_result_text(d) or
                              ElementFinder.find_search_result_analysis_image(d))
            except TimeoutException as e:
                get_logger().info(f"retry: {i+1}")
                time.sleep(1)
                continue
            else:
                break
        else:
            if e:
                raise e

        if not ElementFinder.find_search_result_links(self.browser_driver):
            return results

        while True:
            link: str
            element: WebElement
            for link in [element.get_attribute('href')
                         for element in ElementFinder.find_search_result_links(self.browser_driver)]:
                results.append(self.get_metas_from_search_result_link(link))

            if not ElementFinder.find_next_page_button(self.browser_driver):
                break

            for i in range(100):
                try:
                    ElementFinder.find_next_page_button(self.browser_driver).click()
                    WebDriverWait(self.browser_driver, 10).until(
                        lambda d: ElementFinder.find_search_result_analysis_image(d))
                except TimeoutException as e:
                    get_logger().info(f"retry: {i+1}")
                    time.sleep(1)
                    continue
                else:
                    break
            else:
                if e:
                    raise e
        return results

    def quit(self) -> None:
        if self.config.browser.lower() == 'firefox':
            self.browser_driver.close()
