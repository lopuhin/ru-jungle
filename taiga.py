#!/usr/bin/env python3
import argparse
import gzip
import hashlib
from pathlib import Path
import re
from statistics import mean, median
import tarfile
from typing import List, Dict
import zipfile

import lxml.html
import lxml.etree
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

        break


def get_split(name: str, train_ratio: int) -> str:
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
                    text = clean_subtitles(text)
                    yield split, text


def clean_subtitles(text: str) -> str:
    lines = list(map(clean_subtitles_line, text.splitlines()))
    lines = clean_subtitles_lines(lines)
    return '\n'.join(lines)


def clean_subtitles_line(line: str) -> str:
    cleaned = line.strip('\ufeff')
    del line
    if not cleaned:
        return ''
    if 'www.' in cleaned:
        return ''
    parts = cleaned.split('\t')
    assert len(parts) >= 3
    if len(parts) == 3:
        return ''
    # strip first 3 parts: number, start time, end time
    cleaned = ' '.join(p for p in (p.strip() for p in parts[3:]) if p)
    # strip html
    if '<' in cleaned:
        try:
            cleaned = ''.join(
                lxml.html.fromstring(cleaned).xpath('//text()'))
        except lxml.etree.ParserError:
            cleaned = cleaned.strip('<>')
    # strip remaining timestamps
    cleaned = re.sub(
        r'\d+'
        r'\s+'
        r'\d{2}:\d{2}:\d{2},\d+'
        r'\s+'
        r'-->'
        r'\s+'
        r'\d{2}:\d{2}:\d{2},\d+'
        , '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    if cleaned in {
            '-',
            '.',
            '"идёт перевод"',
            '"перевод редактируется"',
            '- Не переведено -',
        }:
        return ''
    for translate_re in [
            r'^перевод\s',
            r'^перевод:',
            r'^переводчики?:',
            r'^переведено\s',
            r'^внимание\! этот перевод, возможно, ещё не готов',
            r'^серию перевели и озвучили',
            r'^координатор перевода:',
            r'перевод:?\s+-?\s*[a-z]+',
            r'перевод:?\s+-?\s*[a-z]+',
            r'^над переводом работали:',
            r'перевод на русский:',
            r'^автор перевода:',
        ]:
        if re.search(translate_re, cleaned.lower()):
            return ''
    return cleaned.strip()


def clean_subtitles_lines(lines: List[str]) -> List[str]:
    cleaned = []
    for i, line in enumerate(lines):
        line = line.strip()
        next_line = '' if i == len(lines) - 1 else lines[i + 1]
        prev_line = '' if i == 0 else lines[i - 1]
        # remove ... \n ...
        if line.endswith('...') and next_line.startswith('...'):
            line = line.rstrip('...').strip()
        if line.startswith('...') and prev_line.endswith('...'):
            line = line.lstrip('...').strip()
        # join lines starting with lower case letter
        # (but lines with ... are not joined)
        if (i and line and cleaned and
                line[0].isalpha() and line[0].islower() and
                not cleaned[-1].endswith('.')):
            cleaned[-1] = cleaned[-1] + ' ' + line
        else:
            cleaned.append(line)
    return cleaned


if __name__ == '__main__':
    main()
