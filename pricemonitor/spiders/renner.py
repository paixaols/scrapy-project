import scrapy
import time

from datetime import datetime
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


def get_full_exception_name(obj):
    module = obj.__class__.__module__
    if module is None or module == str.__class__.__module__:
        return obj.__class__.__name__
    return module + '.' + obj.__class__.__name__


class RennerSpider(scrapy.Spider):
    name = 'renner'

    max_pagination_depth = 10
    store = 'Renner'

    def start_requests(self):
        urls = [
            ('Feminino-Calça', 'https://www.lojasrenner.com.br/c/feminino/calcas/-/N-14t7lsy?s_icid=230213_MENU_FEM_CALCAS'),
            ('Feminino-Kimono', 'https://www.lojasrenner.com.br/lista/feminino/kimono/-/N-1v2ndciZxv9uau?s_icid=230306_MENU_TREND_FEM_KIMONOS'),
            ('Feminino-Calçado', 'https://www.lojasrenner.com.br/c/feminino/calcados/-/N-1vi7v6o?s_icid=230213_MENU_FEM_CAL%C3%87ADOS'),
            ('Feminino-Cropped', 'https://www.lojasrenner.com.br/c/feminino/blusas-e-camisetas/cropped/-/N-1748jzu?s_icid=230213_MENU_FEM_CROPPEDS'),
            ('Feminino-Casaco/jaqueta', 'https://www.lojasrenner.com.br/c/feminino/casacos-e-jaquetas/-/N-1qn5lks?s_icid=230213_MENU_FEM_CASACOS'),
            ('Feminino-Vestido', 'https://www.lojasrenner.com.br/c/feminino/vestidos/-/N-cg003x?s_icid=230213_MENU_FEM_VESTIDOS')
        ]
        for department, url in urls:
            request = SeleniumRequest(
                url=url,
                callback=self.parse_main,
                cb_kwargs = {
                    'department': department
                }
            )
            yield request

    def parse_main(self, response, department):
        driver = response.meta['driver']
        main_url = response.url
        driver.get(main_url)

        # Número de páginas na paginação
        time.sleep(1)
        number_of_pages = 0
        try:
            number_of_pages = WebDriverWait(driver, timeout=10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/div/div[1]/div[2]/div[2]/div[3]/div[2]/div[3]'))
            ).text
            number_of_pages = int(number_of_pages)
        except Exception as e:
            self.logger.debug(f'{main_url} (Exception: {get_full_exception_name(e)})')
        if number_of_pages > self.max_pagination_depth:
            number_of_pages = self.max_pagination_depth

        for page in range(1, number_of_pages+1):
            url = main_url+f'&page={page}'
            if page > 1:
                driver.get(url)
                time.sleep(2)

            # Identificação da vitrine
            try:
                vitrine = WebDriverWait(driver, timeout=10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/div/div[1]/div[2]/div[2]/div[2]'))
                )
                products = vitrine.find_elements(By.TAG_NAME, 'a')
                self.logger.debug(f'{url} ({len(products)} produtos)')
            except Exception as e:
                self.logger.debug(f'{url} (Exception: {get_full_exception_name(e)})')
                continue
            links = [ p.get_attribute('href') for p in products ]

            # Raspagem dos produtos
            for product_url in links:
                request = SeleniumRequest(
                    url=product_url,
                    callback=self.parse_product,
                    cb_kwargs = {
                        'department': department
                    }
                )
                yield request

    def parse_product(self, response, department):
        driver = response.meta['driver']
        driver.get(response.url)
        time.sleep(2)

        try:
            description = WebDriverWait(driver, timeout=10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/div/div[1]/div[2]/section/div[2]/div[2]/div[1]/div[1]/div[1]/h1'))
            ).text
        except:
            description = None

        details_button = WebDriverWait(driver, timeout=10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="__next"]/div/div[1]/div[2]/section/div[2]/div[3]/div/div[2]/button'))
        )
        details_button.click()
        element = driver.find_element(By.XPATH, '//*[@id="__next"]/div/div[1]/div[2]/section/div[2]/div[3]/div/div[2]/div[2]/div/ul[2]/li[1]')
        try:
            brand = element.text.split(': ')[1]
        except:
            brand = None

        price_div = driver.find_element(By.XPATH, '//*[@id="__next"]/div/div[1]/div[2]/section/div[2]/div[2]/div[1]/div[3]/div/div[1]')
        prices = price_div.find_elements(By.TAG_NAME, 'span')
        if len(prices) == 0:
            old_price = None
            current_price = None
        elif len(prices) == 1:
            old_price = None
            current_price = prices[0].text
            if current_price.lower() == 'indisponível':
                current_price = None
        else:
            old_price = prices[0].text.replace('De ', '')
            current_price = prices[1].text.replace('por ', '')

        try:
            code = driver.find_element(By.XPATH, '//*[@id="__next"]/div/div[1]/div[2]/section/div[2]/div[3]/div/div[2]/div[1]/small').text
            code = code.split(': ')[1]
        except:
            code = None

        yield {
            'store': self.store,
            'department': department,
            'description': description,
            'brand': brand,
            'old_price': old_price,
            'current_price': current_price,
            'code': code,
            'url': response.url,
            'timestamp': datetime.now()
        }
