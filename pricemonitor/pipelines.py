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
                store text,
                department text,
                description text,
                brand text,
                old_price text,
                current_price text,
                code text,
                url text,
                timestamp text
            )
        ''')

    def close_spider(self, spider):
        spider.conn.close()

    def process_item(self, item, spider):
        spider.conn.execute(
            'insert into stage values (?,?,?,?,?,?,?,?,?)',
            (
                item['store'],
                item['department'],
                item['description'],
                item['brand'],
                item['old_price'],
                item['current_price'],
                item['code'],
                item['url'],
                item['timestamp']
            )
        )
        return item
