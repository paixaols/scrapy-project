import scrapy
import time

from datetime import datetime
from scrapy_selenium import SeleniumRequest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


class RennerSpider(scrapy.Spider):
    name = 'renner'

    max_pagination_depth = 30
    store = 'Renner'
    department = ''

    def start_requests(self):
        urls = [
            # ('Feminino-Calça', 'https://www.lojasrenner.com.br/c/feminino/calcas/-/N-14t7lsy?s_icid=230213_MENU_FEM_CALCAS'),
            # ('Feminino-Kimono', 'https://www.lojasrenner.com.br/lista/feminino/kimono/-/N-1v2ndciZxv9uau?s_icid=230306_MENU_TREND_FEM_KIMONOS'),
            ('Feminino-Calçado', 'https://www.lojasrenner.com.br/c/feminino/calcados/-/N-1vi7v6o?s_icid=230213_MENU_FEM_CAL%C3%87ADOS')
        ]
        for department, url in urls:
            self.department = department
            request = SeleniumRequest(
                url=url,
                callback=self.parse_main,
                # cb_kwargs = {
                #     'department': department
                # }
            )
            request.meta['pages'] = 0
            yield request

    def parse_main(self, response):
        driver = response.meta['driver']

        # Número de páginas na paginação
        time.sleep(1)
        number_of_pages = response.meta['pages']
        if number_of_pages == 0:
            try:
                number_of_pages = WebDriverWait(driver, timeout=10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/div/div[1]/div[2]/div[2]/div[3]/div[2]/div[3]'))
                ).text
                number_of_pages = int(number_of_pages)
            except TimeoutException:
                pass
            if number_of_pages > self.max_pagination_depth:
                number_of_pages = self.max_pagination_depth

        # Identifica link dos produtos na página atual
        time.sleep(1)
        try:
            vitrine = WebDriverWait(driver, timeout=10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/div/div[1]/div[2]/div[2]/div[2]'))
            )
            products = vitrine.find_elements(By.TAG_NAME, 'a')
            links = [ p.get_attribute('href') for p in products ]
        except TimeoutException:
            links = []



        # for link in links:
        #     url = response.urljoin(link)
        #     request = scrapy.Request(
        #         url,
        #         callback=self.parse_product
        #     )
        #     yield request
        #     # break


        for link in links:
            url = response.urljoin(link)
            request = SeleniumRequest(
                url=url,
                callback=self.parse_product
            )
            yield request

        # Seguir para próxima página
        urlsplit = response.url.split('&page=')
        if len(urlsplit) == 2:
            current_page = int(urlsplit[1])
        else:
            current_page = 1
        if current_page < number_of_pages:
            next_page = urlsplit[0]+f'&page={current_page+1}'
            request = SeleniumRequest(
                url=next_page,
                callback=self.parse_main,
                # cb_kwargs=dict(department=department)
            )
            request.meta['pages'] = number_of_pages
            yield request

    def parse_product(self, response):
        description = response.xpath('//*[@id="__next"]/div/div[1]/div[2]/section/div[2]/div[2]/div[1]/div[1]/div[1]/h1/span/text()').get()

        attr = response.xpath('//*[@id="__next"]/div/div[1]/div[2]/section/div[2]/div[3]/div/div[2]/div[1]/div/div/a/@href').get()
        try:
            brand = attr.split('/')[4]
        except:
            brand = None

        code = response.xpath('//*[@id="__next"]/div/div[1]/div[2]/section/div[2]/div[3]/div/div[2]/div[1]/small').get()
        if code is not None:
            code = code.split('<!-- -->')[-1].split('</small>')[0]

        product_info = response.xpath('//*[@id="__next"]/div/div[1]/div[2]/section/div[2]/div[2]/div[1]/div[3]/div')
        price_div = response.xpath('//*[@id="__next"]/div/div[1]/div[2]/section/div[2]/div[2]/div[1]/div[3]/div/div[1]')
        prices = price_div.css('span::text').getall()
        if len(prices) == 0:
            old_price = None
            current_price = None
        elif len(prices) == 1:
            old_price = None
            current_price = prices[0]
            if current_price == 'Indisponível':
                current_price = None
        else:
            old_price = prices[0].replace('De ', '')
            current_price = prices[1].replace('por ', '')

        yield {
            'store': self.store,
            'department': self.department,
            'description': description,
            'brand': brand,
            'old_price': old_price,
            'current_price': current_price,
            'code': code,
            'url': response.url,
            'timestamp': datetime.now()
        }
