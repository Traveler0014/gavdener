import re
from typing import Tuple

import requests as req
from lxml import etree

from exts import get_most_like, get_config, log


class MovieInfo:
    default_text = "Unknown"

    def __init__(self, **info):
        self.codename = info.get("codename", self.default_text)
        self.title = info.get("title", self.default_text)
        self.director = info.get("director", self.default_text)
        self.actors = info.get("actors", list())
        self.tags = info.get("tags", list())

    def __str__(self):
        line = '=' * 80
        codename = f'番号:\t{self.codename}'
        title = f'标题:\t{self.title}'
        director = f'导演:\t{self.director}'
        actors = f'演员:\t{"; ".join(self.actors)}'
        tags = f'标签:\t{"; ".join(self.tags)}'
        return "\n".join([line, codename, title, director, actors, tags, line])


class Spider:

    def __init__(self):
        self.baseurl = 'https://www.baidu.com/'
        self.req_conf = dict({
            "headers": {
                "User-Agent":
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.54"
            }
        })

    @property
    def pages(self):
        if not hasattr(self, '_pages'):
            self._pages = dict()
        return self._pages

    def get_html(self,
                 url: str,
                 params: dict = dict(),
                 data: dict = dict(),
                 timeout: int = 3,
                 retry: int = 1):
        try:
            result = self.pages.get(url)
            if result is None:
                while retry > 0:
                    try:
                        cur_page = req.get(url=url,
                                           params=params,
                                           data=data,
                                           timeout=timeout,
                                           **self.req_conf)  # type: ignore
                        assert cur_page.status_code == 200
                        break
                    except:
                        log(f'请求失败: {url}', 'WARNING')
                        retry -= 1
                    finally:
                        if retry <= 0:
                            log(f'请求失败, 不再重试: {url}', 'ERROR')
                if retry > 0:
                    cur_page.encoding = cur_page.apparent_encoding  # type: ignore
                    result = self.pages[url] = cur_page.text  # type: ignore
            return result
        except:
            raise  # TODO 异常处理

    def get_etree(self,
                  url: str,
                  params: dict = dict(),
                  data: dict = dict(),
                  **kwargs):
        html = self.get_html(url, params, data, **kwargs)
        try:
            tree = etree.HTML(html)  # type: ignore
        except ValueError:
            log(f"HTML异常, 不再尝试: {url}", 'ERROR')
            tree = None

        return tree

    def set_proxies(self, proxies: dict):
        self.req_conf['proxies'] = proxies

    def set_cookies(self, cookies: dict):
        self.req_conf['cookies'] = cookies

    def find_by_xpath(self, stmt: str, page: str):
        root_node = etree.HTML(page, etree.HTMLParser)

    def get_info(self, codename: str) -> MovieInfo | None:
        pass


class Javbus(Spider):

    def get_codename(self, text: str) -> str | None:
        res_tree = self.get_etree(f"https://www.javbus.com/search/{text}")
        code_list = [
            i.text for i in res_tree.xpath(
                '//*[@id="waterfall"]/div[*]/a/div[2]/span/date[1]')
        ]
        codename = get_most_like(text, code_list)
        return codename

    def get_movie_info(self, codename: str) -> Tuple[str, str, list, list]:
        # result = [title, director, actors, tags]
        res_tree = self.get_etree(f"https://www.javbus.com/{codename}")
        web_title: str = res_tree.xpath('/html/body/div[5]/h3')[0].text
        title = re.sub(f'{codename}\\s', '', web_title)
        # other info: /html/body/div[5]/div[1]/div[2]/p[*]
        try:
            director = res_tree.xpath(
                '/html/body/div[5]/div[1]/div[2]/p[*]/span[contains(text(), "導演")]/following::a'
            )[0].text
        except:
            director = MovieInfo.default_text
        try:
            actors = [
                actor.text for actor in res_tree.xpath(
                    '/html/body/div[5]/div[1]/div[2]/p[*]/span/a')
            ]
        except:
            actors = list()
        try:
            tags = [
                tag.text for tag in res_tree.xpath(
                    '/html/body/div[5]/div[1]/div[2]/p[*]/span/label/a')
            ]
        except:
            tags = list()
        return title, director, actors, tags

    def get_info(self, name: str) -> MovieInfo | None:
        info = None
        codename = self.get_codename(name)
        if codename is not None:
            info = MovieInfo()
            info.codename = codename
            info.title, info.director, info.actors, info.tags = self.get_movie_info(
                codename)
        return info


if __name__ == "__main__":
    db = Javbus()
    config = get_config()
    db.set_proxies(config.spider.proxy)
    info = db.get_info("SNIS-919")
    print(info)
    print("test...")