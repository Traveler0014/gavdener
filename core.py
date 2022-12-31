import os
import shutil
import traceback
import sys
from typing import List

import spider
from spider import MovieInfo
from exts import log, get_config, file_scanner, get_codename, Config


def get_info(codename: str, config: Config) -> MovieInfo:
    spiders: List[spider.Spider] = list()
    for site in config.spider.resource_sites:
        spider_name = str.capitalize(site).replace(" ", "")
        spiders.append(getattr(spider, spider_name,
                               spider.Javbus)())  # type: ignore
    info = None
    while info is None:
        try:
            site = spiders.pop(0)
            site.set_proxies(config.spider.proxy)
            info = site.get_info(codename)
        except IndexError:
            info = MovieInfo()
        except:
            log(f'获取信息失败, 不再尝试: {codename}', 'ERROR')
            # info = MovieInfo()
            raise

    return info


def move_movie(path: str, info: MovieInfo, config: Config) -> int:
    try:
        assert os.path.isfile(path)
        target_root_dir = config.general.target_dir
        main_actor = info.actors[0] if info.actors else info.default_text
        target_dir = os.path.join(target_root_dir, main_actor, info.codename)
        os.makedirs(target_dir, exist_ok=True)

        filename = os.path.basename(path)

        target_path = os.path.join(target_dir, filename)
        i = 0
        # 确保没有文件会被覆盖
        while os.path.exists(target_path):
            root, ext = os.path.splitext(filename)
            i += 1
            tmp_name = f'{root}-{i}{ext}'
            target_path = os.path.join(target_dir, tmp_name)
        if config.general.debug:
            log(f'移动文件: {path} -> {target_path}', 'debug')
        else:
            log(f'移动文件: {path} -> {target_path}', 'info')
            shutil.move(path, target_path)

        return 0
    except:
        log(traceback.format_exc(), "ERROR")
        return 1

def bar(msg):
    sys.stdout.write(f'{msg}\r')

def main(config: str = None) -> int:  # type: ignore
    if config is None:
        _config = get_config()
    else:
        _config = get_config(config)

    all_movies = file_scanner(target_dir=_config.general.media_dir,
                              include=_config.scrapper.target_exts)
    total = len(all_movies)
    log(f'共扫描到影片{total}部')

    for movie in all_movies:
        bar(f'正在处理: {movie} 进度: {all_movies.index(movie)+1}/{total}')
        log(f"开始处理: {movie}".rjust(128, ">"))
        codename = get_codename(movie)
        try:
            log(f'获取信息: {codename}')
            info = get_info(codename, _config)
            log(f"影片信息:\n{info}")
            if info.codename and info.codename != MovieInfo.default_text:
                move_movie(movie, info, _config)
        except:
            log(f'处理失败: {movie}', 'ERROR')
            # log(traceback.format_exc(), 'ERROR')
            raise
        finally:
            log(f"处理结束: {movie}".rjust(128, "<"))



if __name__ == '__main__':
    main()