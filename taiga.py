#!/usr/bin/env python3
import argparse
import hashlib
from pathlib import Path
from statistics import mean, median
from typing import List, Dict
import zipfile

import tqdm


ARCHIVES = [
    'news.zip',
    'Subtitles.tar.gz',
    'social.tar.gz',
]


def main():
    parser = argparse.ArgumentParser()
    arg = parser.add_argument
    arg('taiga_root', type=Path,
        help=f'folder with taiga corpus files as archives: '
        f'{" ".join(ARCHIVES)}')
    arg('target', type=Path,
        help='folder where to put train, valid and test files')
    arg('--split-ratio', type=int,
        help='Raio of train data relative to test or valid')
    args = parser.parse_args()

    for name in ARCHIVES:
        path: Path = args.taiga_root / name
        if not path.exists():
            print(f'{path} not found, skipping')
            continue
        print(f'Reading {path}')
        if path.suffix == '.zip':
            reader = zip_reader
        else:
            raise ValueError

        split_files = {}
        for split in ['train', 'valid', 'test']:
            split_path = args.target / path.name.split('.')[0] / f'{split}.txt'
            split_path.parent.mkdir(exist_ok=True, parents=True)
            split_files[split] = split_path.open('wt', encoding='utf8')

        try:
            stats = []
            stats_by_split = {}
            for name, text in reader(path):
                text = text.strip()
                if not text:
                    continue
                s = {
                    'name': name,
                    'chars': len(text),
                    'lines': len(text.split('\n')),
                    'words': len(text.split(' ')),
                }
                stats.append(s)
                split = get_split(name)
                stats_by_split.setdefault(split, []).append(s)
                split_files[split].write(text)
                split_files[split].write('\n\n\n')
        finally:
            for f in split_files.values():
                f.close()

        print_stats(stats, 'all')
        for split, split_stats in sorted(stats_by_split.items()):
            print_stats(split_stats, split)


def get_split(name: str, train_ratio: int=20) -> str:
    n = sum(hashlib.md5(name.encode('utf8')).digest()) % train_ratio
    return {0: 'test', 1: 'valid'}.get(n, 'train')


def print_stats(stats: List[Dict], name: str):
    print(f'\n{len(stats)} {name}:')
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


def zip_reader(path: Path):
    with zipfile.ZipFile(path, 'r') as f:
        for name in tqdm.tqdm(f.namelist(), desc=str(path)):
            if '/texts/' in name and '.' in name:
                _, ext = name.rsplit('.', 1)
                if ext == 'txt':
                    text = f.read(name).decode('utf8')
                    yield name, text
                elif ext == 'csv':
                    pass
                else:
                    raise ValueError(f'Unexpected extension for {name}')


if __name__ == '__main__':
    main()
