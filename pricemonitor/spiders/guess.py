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


class GuessSpider(scrapy.Spider):
    name = 'guess'

    max_pagination_depth = 10
    store = 'Guess'

    def start_requests(self):
        urls = [
            ('Feminino-Blusa', 'https://www.guessbrasil.com.br/feminino/roupas/blusas'),
            ('Feminino-Calça', 'https://www.guessbrasil.com.br/feminino/roupas/calcas'),
            ('Feminino-Calça jeans', 'https://www.guessbrasil.com.br/feminino/roupas/calcas-jeans'),
            ('Feminino-Casaco/jaqueta', 'https://www.guessbrasil.com.br/feminino/roupas/casacos-e-jaquetas'),
            ('Feminino-Moleton', 'https://www.guessbrasil.com.br/feminino/roupas/moletons'),
            ('Feminino-Vestido', 'https://www.guessbrasil.com.br/feminino/roupas/vestidos')
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
        driver.get(response.url)

        # Número de páginas na paginação
        time.sleep(1)
        number_of_pages = 0
        try:
            elements = WebDriverWait(driver, timeout=10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@class="page-number"]'))
            ).find_elements(By.TAG_NAME, 'span')
            number_of_pages = int(elements[-2].text)
        except Exception as e:
            self.logger.debug(f'{response.url} (Exception: {get_full_exception_name(e)})')
        if number_of_pages > self.max_pagination_depth:
            number_of_pages = self.max_pagination_depth

        for page in range(1, number_of_pages+1):
            url = response.url+f'#/pagina-{page}'
            if page > 1:
                driver.get(url)
                time.sleep(2)

            # Identificação da vitrine
            try:
                vitrine = WebDriverWait(driver, timeout=10).until(
                    EC.presence_of_element_located((By.XPATH, '//div[2]/div/div/div[2]/article/div/ul'))
                )
                products = vitrine.find_elements(By.TAG_NAME, 'li')
                self.logger.debug(f'{url} ({len(products)} produtos)')
            except Exception as e:
                self.logger.debug(f'{url} (Exception: {get_full_exception_name(e)})')
                continue

            # Raspagem dos produtos
            for p in products:
                info_el = p.find_element(By.XPATH, 'div[2]/div[4]')

                e = info_el.find_element(By.XPATH, 'span/a')
                product_url = e.get_attribute('href')
                description = e.text

                price_el = info_el.find_element(By.XPATH, 'div[2]/div')
                try:
                    old_price = price_el.find_element(By.XPATH, 'del').text
                    current_price = price_el.find_element(By.XPATH, 'strong').text
                    current_price = current_price.split(' (')[0]
                except:
                    old_price = None
                    current_price = price_el.find_element(By.XPATH, 'strong').text

                yield {
                    'store': self.store,
                    'department': department,
                    'description': description,
                    'brand': None,
                    'old_price': old_price,
                    'current_price': current_price,
                    'code': None,
                    'url': product_url,
                    'timestamp': datetime.now()
                }
