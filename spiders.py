import re
import traceback
from urllib.parse import quote
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

    def to_dict(self):
        return dict(codename=self.codename,
                    title=self.title,
                    director=self.director,
                    actors=self.actors,
                    tags=self.tags)


class Spider:
    baseurl = 'https://www.baidu.com/'

    def __init__(self):
        self.req_conf = dict({
            "headers": {
                "User-Agent":
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.54"
            }
        })

    @property
    def infos(self) -> dict:
        if not hasattr(self, "_infos"):
            self._infos = dict()
        return self._infos

    @property
    def pages(self):
        if not hasattr(self, '_pages'):
            self._pages = dict()
        return self._pages

    def get_html(self,
                 url: str,
                 params: dict = dict(),
                 data: dict = dict(),
                 timeout: int = 5,
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
                        # log(traceback.format_exc(), "ERROR")
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

    def get_list_by_xpath(self, url: str, stmt: str):
        res_tree = self.get_etree(url)
        if res_tree is None:
            return list()
        else:
            return [i for i in res_tree.xpath(stmt)]

    def get_codename(self, text: str) -> Tuple[str, str] | str | None:
        pass

    def get_movie_info(
            self,
            codename: str) -> Tuple[str, str, list, list]:  # type: ignore
        pass

    def get_info(self, name: str) -> MovieInfo | None:
        # 检查是否已有缓存
        if self.infos.get(name):
            return self.infos[name]

        info = None
        result = self.get_codename(name)
        codename = result[0] if isinstance(result, tuple) else result
        if codename is not None:
            uri = result[1] if isinstance(result, tuple) else codename

            info = MovieInfo()
            info.codename = codename
            info.title, info.director, info.actors, info.tags = self.get_movie_info(
                uri)
        self.infos[codename] = info
        return info


class Javbus(Spider):
    baseurl = 'https://www.javbus.com'

    def get_codename(self, text: str) -> str | None:

        def _get_code_list(url: str):
            res_tree = self.get_etree(url)
            if res_tree is None:
                return list()
            else:
                return [
                    i.text for i in res_tree.xpath(
                        '//*[@id="waterfall"]/div[*]/a/div[2]/span/date[1]')
                ]

        code_list = _get_code_list(
            f"{self.baseurl}/search/{quote(text, encoding='utf-8')}")

        if not code_list:  # 找不到,有可能因为是无码
            code_list = _get_code_list(
                f"{self.baseurl}/uncensored/search/{quote(text, encoding='utf-8')}"
            )
        codename = get_most_like(text, code_list)
        return codename

    def get_movie_info(self, codename: str) -> Tuple[str, str, list, list]:
        # result = [title, director, actors, tags]
        res_tree = self.get_etree(
            f"https://www.javbus.com/{quote(codename, encoding='utf-8')}")

        if res_tree is None:
            return MovieInfo.default_text, MovieInfo.default_text, list(
            ), list()

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


class Javdb(Spider):
    baseurl = 'https://javdb.com'

    def get_codename(self, text: str) -> Tuple[str, str] | None:

        query_url = f"{self.baseurl}/search?q={quote(text, encoding='utf-8')}"

        node_list = self.get_list_by_xpath(
            query_url, '/html/body/section/div/div[6]/div')
        code_url = {
            node.xpath('a/div[2]/strong')[0].text:
            node.xpath('a')[0].attrib['href']
            for node in node_list
        }
        code_list = list(code_url.keys())
        codename = get_most_like(text, code_list)

        if codename is None:
            return None
        else:
            uri = code_url[codename]
            return codename, uri

    def get_movie_info(self, uri: str) -> Tuple[str, str, list, list]:
        # result = [title, director, actors, tags]
        res_tree = self.get_etree(
            f"{self.baseurl}{quote(uri, encoding='utf-8')}")

        if res_tree is None:
            return MovieInfo.default_text, MovieInfo.default_text, list(
            ), list()

        title = res_tree.xpath(
            '/html/body/section/div/div[4]/h2/strong[2]')[0].text
        # other_info = /html/body/section/div/div[4]/div[1]/div/div[2]
        try:
            director = res_tree.xpath(
                '/html/body/section/div/div[4]/div[1]/div/div[2]/nav/div/strong[contains(text(), "導演")]/following-sibling::span/a'
            )[0].text
        except:
            director = MovieInfo.default_text
        try:
            actor_nodes = res_tree.xpath(
                '/html/body/section/div/div[4]/div[1]/div/div[2]/nav/div/strong[contains(text(), "演員")]'
            )[0].xpath('following-sibling::span/a')
            actors = [
                actor.text for actor in actor_nodes if 'female' in actor.xpath(
                    'following-sibling::strong')[0].attrib["class"]
            ]
        except:
            actors = list()
        try:
            tag_nodes = res_tree.xpath(
                '/html/body/section/div/div[4]/div[1]/div/div[2]/nav/div/strong[contains(text(), "類別")]'
            )[0].xpath('following-sibling::span/a')
            tags = [tag.text for tag in tag_nodes]
        except:
            tags = list()
        return title, director, actors, tags


if __name__ == "__main__":
    db = Javdb()
    config = get_config()
    db.set_proxies(config.spider.proxy)
    info = db.get_info("SNIS-919")
    # info = db.get_info("SNIS-919")
    print(info)
    print("test...")