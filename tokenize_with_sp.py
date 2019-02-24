#!/usr/bin/env python3
import argparse
from pathlib import Path

import sentencepiece as spm


def main():
    parser = argparse.ArgumentParser()
    arg = parser.add_argument
    arg('source')
    arg('target')
    arg('sp_model', help='sentencepiece model')
    args = parser.parse_args()

    sp = spm.SentencePieceProcessor()
    sp.Load(args.sp_model)

    for corpus_folder in Path(args.source).iterdir():
        if not corpus_folder.is_dir():
            continue
        for source_path in corpus_folder.glob('*.txt'):
            target_path = (
                Path(args.target) / corpus_folder.name / source_path.name)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with target_path.open('wt', encoding='utf8') as outf, \
                    source_path.open('rt', encoding='utf8') as f:
                for line in f:
                    outf.write(' '.join(sp.EncodeAsPieces(line.strip())))
                    outf.write('\n')


if __name__ == '__main__':
    main()
