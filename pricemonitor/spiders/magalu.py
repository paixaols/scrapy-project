import scrapy
import time

from datetime import datetime
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


def retry_get_attribute(element, attribute, attempts=5, sleep=1):
    '''
    Retrieve an attribute from a Selenium WebElement object.
    Try repeated times with a wait time between attempts.
    Returns the attribute if any attempt succeeds, otherwise returns None.
    '''
    attempt = 1
    while attempt < attempts:
        try:
            result = element.get_attribute(attribute)
            break
        except:
            attempt += 1
        time.sleep(sleep)
    else:
        return None
    return result


class QuotesSpider(scrapy.Spider):
    name = 'magalu'

    def start_requests(self):
        urls = [
            'https://www.magazineluiza.com.br/celulares-e-smartphones/l/te/',
            'https://www.magazineluiza.com.br/tv-e-video/l/et/'
        ]
        for url in urls:
            yield SeleniumRequest(
                url=url,
                callback=self.parse_main
            )
        # url = 'https://www.magazineluiza.com.br/smart-tv-32-hd-led-semp-r6500-wi-fi-3-hdmi-1-usb/p/235912900/et/elit/'
        # yield scrapy.Request(url, self.parse_product)

    def parse_main(self, response):
        driver = response.meta['driver']

        time.sleep(1)

        # Número de páginas na paginação
        pagination_ul = WebDriverWait(driver, timeout=10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/div/main/section[4]/div[5]/nav/ul'))
        )
        pages = pagination_ul.find_elements(By.TAG_NAME, 'li')
        number_of_pages = pages[-2].text
        number_of_pages = int(number_of_pages)

        time.sleep(1)

        # Identifica link dos produtos na página atual
        products_ul = WebDriverWait(driver, timeout=10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="__next"]/div/main/section[4]/div[4]/div/ul'))
        )
        time.sleep(1)
        products = products_ul.find_elements(By.TAG_NAME, 'li')
        links = [ retry_get_attribute(p.find_element(By.TAG_NAME, 'a'), 'href') for p in products ]

        for link in links:
            yield response.follow(link, callback=self.parse_product)

        # Seguir para próxima página
        urlsplit = response.url.split('?page=')
        if len(urlsplit) == 2:
            current_page = int(urlsplit[1])
        else:
            current_page = 1
        if current_page < number_of_pages:
            next_page = response.url.split('?')[0]+f'?page={current_page+1}'
            yield SeleniumRequest(
                url=next_page,
                callback=self.parse_main
            )

    def parse_product(self, response):
        description = response.css('h1::text').get()
        code = response.xpath('//*[@id="__next"]/div/main/section[2]/div[2]/span/span[1]').get()
        if code is not None:
            code = code.split('<!-- -->')[-1].split('</span>')[0]
        brand = response.xpath('//*[@id="__next"]/div/main/section[2]/div[2]/span/a/text()').get()
        price = response.css('p[data-testid="price-value"]::text').get()

        yield {
            'description': description,
            'brand': brand,
            'price': price,
            'code': code,
            'url': response.url,
            'timestamp': datetime.now()
        }
