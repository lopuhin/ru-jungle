#!/usr/bin/env python3
import argparse
import gzip
from functools import partial
import hashlib
from pathlib import Path
import re
from statistics import mean, median
import tarfile
from typing import List, Dict, Optional
import zipfile

import lxml.html
import lxml.etree
import tqdm


def main():
    ARCHIVES = [
        ('rnc-main', 'ruscorpora.tar.gz', partial(rnc_reader, corpus='main')),
        ('rnc-paper', 'ruscorpora.tar.gz', partial(rnc_reader, corpus='paper')),
        ('taiga-subtitles', 'Subtitles.tar.gz', taiga_subtitles_reader),
        ('taiga-news', 'news.zip', taiga_news_reader),
        # ('taiga-social', 'social.tar.gz', taiga_social_reader),
    ]

    parser = argparse.ArgumentParser()
    arg = parser.add_argument
    arg('root', type=Path,
        help=f'folder with corpus files as archives, supported: '
        f'{" ".join(sorted({f for _, f, _ in ARCHIVES}))}')
    arg('target', type=Path,
        help='folder where to put train, valid and test files')
    arg('--train-ratio', type=int, default=20,
        help='Ratio of train data relative to test or valid: e.g. with default '
             'value of %(default)s, train will be approximately '
             '%(default)s times bigger than test and '
             '%(default)s times bigger than valid.')
    args = parser.parse_args()

    for out_name, in_name, reader in ARCHIVES:
        path: Path = args.root / in_name
        if not path.exists():
            print(f'{path} not found, skipping')
            continue
        split_files = {}
        for split in ['train', 'valid', 'test']:
            split_path: Path = args.target / out_name / f'{split}.txt'
            split_path.parent.mkdir(exist_ok=True, parents=True)
            split_files[split] = split_path.open('wt', encoding='utf8')

        print(f'Reading {path} ({out_name})')
        try:
            stats = []
            stats_by_split = {}
            for group, text in reader(path):
                text = text.strip()
                if not text:
                    continue
                s = {'group': group,
                     'chars': len(text),
                     'lines': len(text.split('\n')),
                     'words': len(text.split(' '))}
                stats.append(s)
                split = get_split(group, train_ratio=args.train_ratio)
                stats_by_split.setdefault(split, []).append(s)
                split_files[split].write(text)
                split_files[split].write('\n\n\n')
        finally:
            for f in split_files.values():
                f.close()

        print_stats(stats, 'all')
        for split in ['train', 'valid', 'test']:
            print_stats(stats_by_split[split], split)


def get_split(name: str, train_ratio: int) -> str:
    n = sum(hashlib.md5(name.encode('utf8')).digest()) % train_ratio
    return {0: 'test', 1: 'valid'}.get(n, 'train')


def print_stats(stats: List[Dict], name: str):
    n_groups = len({s['group'] for s in stats})
    print(f'\n{len(stats)} texts, {n_groups} groups in {name}:')
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


def taiga_news_reader(path: Path):
    """ Read taiga news corpus, yield (split, text) pairs.
    Split is done by name.
    """
    assert path.suffix == '.zip'
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


def taiga_subtitles_reader(path: Path):
    """ Read taiga subtitles, yield (group, text) pairs.
    Split is done by series name (all episodes are in one split).
    """
    assert path.name.endswith('.tar.gz')
    with gzip.open(path) as gz:
        with tarfile.TarFile(fileobj=gz) as f:
            for member in tqdm.tqdm(f.getmembers()):
                name = member.name
                if name.endswith('.ru.txt') and 'Subtitles/texts/' in name:
                    _, rel_name = name.split('Subtitles/texts/', 1)
                    series, _episode = rel_name.split('/')
                    text = f.extractfile(member).read().decode('utf8')
                    text = clean_subtitles(text)
                    yield series, text


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
    cleaned_lower = cleaned.lower()
    if 'перев' in cleaned_lower:
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
            if re.search(translate_re, cleaned_lower):
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


def taiga_social_reader(path: Path):
    """ Read taiga social corpus, yield (group, text) pairs.
    Split is done by series name (all episodes are in one split).
    """
    # FIXME not used
    # TODO also twitter and LJ
    assert path.name.endswith('.tar.gz')
    with gzip.open(path) as gz:
        with tarfile.TarFile(fileobj=gz) as f:
            for member in f.getmembers():
                if member.name.endswith('/texts/fbtexts.txt') or \
                        member.name.endswith('/tests/vktexts.txt'):
                    yield from fbvk_reader(f.extractfile(member))


def fbvk_reader(f):
    # FIXME not used: handle authors (especially vk), likes, etc.
    item_id = None
    item = []
    for line in f:
        line = line.decode('utf8')
        line = line.strip('\ufeff').strip()
        if line.startswith('DataBaseItem: ') and len(line.split()) == 2:
            if item_id is not None:
                yield item_id, '\n'.join(item)
            _, item_id = line.split()
            item = []
        else:
            item.append(line)


def rnc_reader(path: Path, corpus: str):
    assert path.name.endswith('.tar.gz')
    with gzip.open(path) as gz:
        with tarfile.TarFile(fileobj=gz) as f:
            for member in tqdm.tqdm(f.getmembers()):
                name = member.name
                if '/' not in name:
                    continue
                _, corp = name.split('/')[:2]
                if corp != corpus:
                    continue
                if not (name.endswith('.xhtml') or name.endswith('.xml')):
                    continue
                try:
                    root = lxml.etree.parse(f.extractfile(member)).getroot()
                except Exception as e:
                    print(f'Failed to parse {name}: {e}')
                    continue
                text = rnc_file_reader(root)
                if text is not None:
                    yield name, text


def rnc_file_reader(root) -> Optional[str]:
    if any(el.get('content') == 'manual' for el in root.findall('.//meta')):
        return None  # can't properly recover punctuation
    elif root.findall('.//ana'):
        return None  # can't properly recover punctuation
    else:
        ns_match = re.match(r'{.*}', root.tag)
        ns = ns_match.group(0) if ns_match else ''
        body = root.find(f'{ns}body')
        return ''.join(body.xpath('.//text()')).strip().replace('--', '—')


if __name__ == '__main__':
    main()
