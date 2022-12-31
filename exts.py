import os
import re
from typing import Any, List
from difflib import SequenceMatcher, get_close_matches

import yaml


def log(msg: str, level: str = "i"):
    with open("gavdener.log", "a", encoding='utf-8') as fp:
        fp.write(f'[{level[0].lower()}]::{msg}\n')


class Config(dict):

    def __init__(self, data: dict = dict()):
        super().__init__(data)

    def __getattribute__(self, __name: str) -> Any:
        try:
            attr = object.__getattribute__(self, __name)
            return attr
        except AttributeError:
            res = self.get(__name)
            if res is None:
                raise
            elif isinstance(res, dict):
                return Config(res)
            else:
                return res


def get_config(path: str = 'config.yaml'):

    def _read_config(path):
        with open(path, 'r', encoding='utf-8') as fp:
            # config = yaml.Loader(fp).get_data()
            config = Config(yaml.Loader(fp).get_data())
        return config

    if os.path.isfile(path):
        return _read_config(path)
    else:
        default_config = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), 'config.yaml')
        log(
            f"unable to read specified config file, load default settings: {default_config}",
            'WARNING')
        return _read_config(default_config)


def file_scanner(target_dir: str,
                 include: list = list(),
                 exclude: list = list(),
                 func=lambda x: os.path.splitext(x)[1]) -> List[str]:
    result = list()

    for parent_dir, dirs, files in os.walk(target_dir):

        _parent_dir = os.path.relpath(parent_dir, target_dir)

        if files:
            if 'gavdener.ignore' in files:
                continue
            for file in files:
                if include and func(file) not in include:
                    continue
                if exclude and func(file) in exclude:
                    continue
                result.append(
                    os.path.join(os.path.realpath(target_dir), _parent_dir,
                                 file))
        elif dirs:
            pass
        else:
            # result.append(os.path.join(os.path.realpath(target_dir), _parent_dir))
            pass
    return result


def common_part(text1: str, text2: str, ret_id: int = -1) -> str:
    astart, bstart, size = SequenceMatcher(a=text1,
                                           b=text2).find_longest_match()
    # print(part.groups())
    if size < 5:
        if ret_id not in (0, 1):
            return min(text1, text2)
        else:
            return (text1, text2)[ret_id]
    else:
        return text1[astart:astart + size]


def get_codename(filepath: str) -> str:
    filename = os.path.basename(filepath)
    filedir = os.path.dirname(filepath)

    name = common_part(filename, filedir, 0)

    codename = None

    matcher = [
        re.compile(r'(FC|fc)2[-_]?((PPV|ppv)[-_])?\d{6,7}'),  # FC2番号
        re.compile(
            r'((?<=[^A-Za-z])|^)([A-Z]|[a-z]){2,5}[-_]?\d{3,5}(?!(\d|[A-Za-z0-9]{3,}))'
        ),  # 常见番号
        re.compile(
            r'((?<=[^A-Za-z0-9])|^)\d{6,7}[-_]\d{3,4}(?!(\d|[A-Za-z0-9]{3,}))'
        )  # 无码番号: 一本道/加勒比
    ]

    while codename is None:
        try:
            match_res = re.search(matcher.pop(0), name)
            if match_res is not None:
                codename = match_res.group(0)
        except IndexError:
            codename = os.path.splitext(filename)[0]
            # codename = filename

    return codename


def get_most_like(text: str, possibilities: list) -> str | None:
    cmp_text = text.casefold()
    cmp_list = list(map(str.casefold, possibilities))
    result = get_close_matches(cmp_text, cmp_list, n=3, cutoff=0.4)
    if result:
        res_idx = cmp_list.index(result[0])
        return possibilities[res_idx]
    else:
        return None


if __name__ == "__main__":
    a = get_config()
    lst = file_scanner(r"F:\Watch\AD", include=a.scrapper.target_exts)
    print(lst)
    # b = get_codename(r"F:\Watch\AD\FC2-PPV-3087371\hhd800.com@FC2-PPV-3087371.mp4")
    for i in lst:
        print(get_codename(i))
    print('debug...')
