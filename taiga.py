#!/usr/bin/env python3
import argparse
import gzip
import hashlib
from pathlib import Path
from statistics import mean, median
import tarfile
from typing import List, Dict
import zipfile

import tqdm


ARCHIVES = [
    'Subtitles.tar.gz',
    'social.tar.gz',
    'news.zip',
]


def main():
    parser = argparse.ArgumentParser()
    arg = parser.add_argument
    arg('taiga_root', type=Path,
        help=f'folder with taiga corpus files as archives: '
        f'{" ".join(ARCHIVES)}')
    arg('target', type=Path,
        help='folder where to put train, valid and test files')
    arg('--train-ratio', type=int, default=20,
        help='Ratio of train data relative to test or valid: e.g. with default '
             'value of %(default)s, train will be approximately '
             '%(default)s times bigger than test and '
             '%(default)s times bigger than valid.')
    args = parser.parse_args()

    for name in ARCHIVES:
        path: Path = args.taiga_root / name
        if not path.exists():
            print(f'{path} not found, skipping')
            continue
        split_files = {}
        for split in ['train', 'valid', 'test']:
            split_path: Path = (
                args.target /
                path.name.lower().split('.')[0] /
                f'{split}.txt')
            split_path.parent.mkdir(exist_ok=True, parents=True)
            split_files[split] = split_path.open('wt', encoding='utf8')

        print(f'Reading {path}')
        reader = {
            'news.zip': news_reader,
            'Subtitles.tar.gz': subtitles_reader,
        }[name]

        try:
            stats = []
            stats_by_split = {}
            for split, text in reader(path, train_ratio=args.train_ratio):
                text = text.strip()
                if not text:
                    continue
                s = {'chars': len(text),
                     'lines': len(text.split('\n')),
                     'words': len(text.split(' '))}
                stats.append(s)
                stats_by_split.setdefault(split, []).append(s)
                split_files[split].write(text)
                split_files[split].write('\n\n\n')
        finally:
            for f in split_files.values():
                f.close()

        print_stats(stats, 'all')
        for split in ['train', 'valid', 'test']:
            print_stats(stats_by_split[split], split)


def get_split(name: str, train_ratio: int=20) -> str:
    n = sum(hashlib.md5(name.encode('utf8')).digest()) % train_ratio
    return {0: 'test', 1: 'valid'}.get(n, 'train')


def print_stats(stats: List[Dict], name: str):
    print(f'\n{len(stats)} texts in {name}:')
    for key in ['chars', 'words', 'lines']:
        values = sorted(s[key] for s in stats)
        print(f'{key}: '
              f'mean: {mean(values):.1f} '
              f'| min: {min(values)} '
              f'| median: {median(values)} '
              f'| 95%: {values[int(len(values) * 0.95)]} '
              f'| 99%: {values[int(len(values) * 0.99)]} '
              f'| max: {max(values)} '
              f'| sum: {sum(values):,}')


def news_reader(path: Path, train_ratio: int):
    """ Read taiga news corpus, yield (split, text) pairs.
    Split is done by text.
    """
    assert path.suffix == '.zip'
    with zipfile.ZipFile(path, 'r') as f:
        for name in tqdm.tqdm(f.namelist(), desc=str(path)):
            if '/texts/' in name and '.' in name:
                _, ext = name.rsplit('.', 1)
                if ext == 'txt':
                    text = f.read(name).decode('utf8')
                    split = get_split(name, train_ratio=train_ratio)
                    yield split, text
                elif ext == 'csv':
                    pass
                else:
                    raise ValueError(f'Unexpected extension for {name}')


def subtitles_reader(path: Path, train_ratio: int):
    """ Read taiga subtitles, yield (split, text) pairs.
    Split is done by series name (all episodes are in one split).
    """
    assert path.name.endswith('.tar.gz')
    with gzip.open(path) as gz:
        with tarfile.TarFile(fileobj=gz) as f:
            for member in tqdm.tqdm(f.getmembers()):
                name = member.name
                if name.endswith('.ru.txt') and 'Subtitles/texts/' in name:
                    _, rel_name = name.split('Subtitles/texts/', 1)
                    series, episode = rel_name.split('/')
                    split = get_split(series, train_ratio=train_ratio)
                    text = f.extractfile(member).read().decode('utf8')
                    yield split, text


if __name__ == '__main__':
    main()
