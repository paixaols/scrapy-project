# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from sqlalchemy import create_engine


class PricemonitorPipeline:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            db_connection=crawler.settings.get('DATABASE_CONNECTION')
        )

    def open_spider(self, spider):
        engine = create_engine(self.db_connection)
        spider.conn = engine.connect()
        spider.conn.execute('drop table if exists stage')
        spider.conn.execute('''
            create table stage (
                description text,
                brand text,
                price text,
                code text,
                url text,
                timestamp text
            )
        ''')

    def close_spider(self, spider):
        spider.conn.close()

    def process_item(self, item, spider):
        spider.conn.execute(
            'insert into stage values (?,?,?,?,?,?)',
            (
                item['description'],
                item['brand'],
                item['price'],
                item['code'],
                item['url'],
                item['timestamp']
            )
        )
        return item
