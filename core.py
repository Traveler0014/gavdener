import os
import shutil
import traceback
import sys
from typing import List

import yaml

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
            # raise

    return info


def set_mark(
        path: str,
        info: MovieInfo = None,  # type: ignore
        ignore_file: str = 'gavdener.ignore',
        info_file: str = 'info.yaml'):
    if os.path.isdir(path):
        target_dir = path
    else:
        target_dir = os.path.dirname(path)
    if not os.path.isdir(target_dir):
        log(f'停止添加标记, 目标路径未指向目录或文件: {path}', 'WARNING')
        return 1

    if info is None:
        filename = ignore_file
    else:
        filename = info_file
    target_path = os.path.join(target_dir, filename)
    with open(target_path, "w", encoding='utf-8') as fp:
        if info is None:
            log(f'标记为无效路径: {target_dir}')
        else:
            log(f'添加标记: {target_dir}')
            yaml_info = yaml.dump(info.to_dict(),
                                  indent=2,
                                  allow_unicode=True,
                                  sort_keys=False)
            fp.write(yaml_info)
    return 0


def move_movie(path: str, info: MovieInfo, config: Config) -> int:
    try:
        assert os.path.isfile(path)
        target_root_dir = config.general.target_dir
        main_actor = info.actors[0] if info.actors else info.default_text
        other_actors = info.actors[1:] if len(info.actors) > 1 else list()
        target_dir = os.path.join(target_root_dir, main_actor, info.codename)
        os.makedirs(target_dir, exist_ok=True)

        filename = os.path.basename(path)

        target_path = os.path.join(target_dir, filename)
        i = 0
        # 确保没有文件会被覆盖
        is_same = False
        while os.path.exists(target_path):
            log(f'文件已存在: {target_path}')
            if os.stat(path).st_ino == os.stat(target_path).st_ino:
                log(f'文件指向相同: {path} == {target_path}')
                is_same = True
                break
            root, ext = os.path.splitext(filename)
            i += 1
            tmp_name = f'{root}-{i}{ext}'
            target_path = os.path.join(target_dir, tmp_name)
        if config.general.debug:
            log(f'移动文件: {path} -> {target_path}', 'debug')
            set_mark(target_path,
                     info,
                     ignore_file=config.general.ignore_file,
                     info_file=config.general.info_file)
        else:
            log(f'移动文件: {path} -> {target_path}', 'info')
            if is_same:
                log(f'文件已存在, 仅补充信息: {target_path}')
                set_mark(target_path,
                         info,
                         ignore_file=config.general.ignore_file,
                         info_file=config.general.info_file)
            else:
                set_mark(target_path,
                         info,
                         ignore_file=config.general.ignore_file,
                         info_file=config.general.info_file)
                shutil.move(path, target_path)

        # 创建链接
        if config.scrapper.multi_actors:
            for actor in other_actors:
                tmp_dir = os.path.join(target_root_dir, actor, info.codename)
                os.makedirs(tmp_dir, exist_ok=True)
                tmp_path = os.path.join(tmp_dir, filename)
                if os.path.isfile(
                        target_path) and not os.path.exists(tmp_path):
                    log(f'创建链接: {tmp_path} -> {target_path}')
                    os.link(target_path, tmp_path)
                set_mark(tmp_path,
                         info,
                         ignore_file=config.general.ignore_file,
                         info_file=config.general.info_file)
        return 0
    except:
        log(traceback.format_exc(), "ERROR")
        return 1


def bar(msg):
    sys.stdout.write(f'\r{msg}'.ljust(128, " "))
    sys.stdout.flush()


def main(config: str = None) -> int:  # type: ignore
    if config is None:
        _config = get_config()
    else:
        _config = get_config(config)

    all_movies = file_scanner(target_dir=_config.general.media_dir,
                              include=_config.scrapper.target_exts,
                              ignore_file=_config.general.ignore_file)
    total = len(all_movies)
    log(f'共扫描到影片{total}部')

    for movie in all_movies:
        bar(f'正在处理: {movie} 进度: {all_movies.index(movie)+1}/{total}')
        log(f"开始处理: {movie}".rjust(128, ">"))
        codename = get_codename(movie, _config.general.info_file)
        try:
            log(f'获取信息: {codename}')
            info = get_info(codename, _config)
            log(f"影片信息:\n{info}")
            if info.codename and info.codename != MovieInfo.default_text:
                move_movie(movie, info, _config)
            else:
                set_mark(movie,
                         ignore_file=_config.general.ignore_file,
                         info_file=_config.general.info_file)
        except:
            log(f'处理失败: {movie}', 'ERROR')
            # log(traceback.format_exc(), 'ERROR')
            raise
        finally:
            log(f"处理结束: {movie}".rjust(128, "<"))


if __name__ == '__main__':
    main()