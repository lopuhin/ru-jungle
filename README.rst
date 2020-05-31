RU-Jungle: collection of Russian corpora for language model training
====================================================================

This project prepares clean text corpora for language model training,
including a train/valid/test split.

Installation
------------

Use Python 3.6+, install requirements from ``requirements.txt``.

Usage
-----

Source corpora
++++++++++++++

Put all corpora in one folder, ``./corpora`` is used as an example below.
All parts are optional.

- Taiga corpora: download subtitles and news from
  https://tatianashavrina.github.io/taiga_site/downloads,
  expected file names are ``Subtitles.tar.gz`` and ``news.zip``.
  Also supported ``proza_ru.zip`` which you can obtain by downloading
  and extracting the full corpus file.
- RNC corpus: expected file name is ``ruscorpora.tar.gz``
- Russian Wikipedia: download the dump::

    wget http://dumps.wikimedia.org/ruwiki/latest/ruwiki-latest-pages-articles.xml.bz2

  then parse it::

    cd wikiextractor
    ./WikiExtractor.py ../ruwiki-latest-pages-articles.xml.bz2 --processes 8 --json \
        --output ../corpora/ruwiki --compress --min_text_length 100 --quiet


Creating corpora with all texts in one file
+++++++++++++++++++++++++++++++++++++++++++

- Create text::

    ./main.py ./corpora/ ./out-balanced/

  optionally it's possible to keep each document as a separate file (see next section)::

    ./main.py ./corpora/ ./out-as-files/ --as-files

- Collect train, test and valid across subcorpora::

    $ cat out-balanced/*/test.txt > out-balanced/test.txt
    $ cat out-balanced/*/valid.txt > out-balanced/valid.txt
    $ cat out-balanced/*/train.txt > out-balanced/train.txt

- Expected result::

    out-balanced/
    ├── rnc-main
    │   ├── test.txt
    │   ├── train.txt
    │   └── valid.txt
    ├── rnc-paper
    │   ├── test.txt
    │   ├── train.txt
    │   └── valid.txt
    ├── taiga-news
    │   ├── test.txt
    │   ├── train.txt
    │   └── valid.txt
    ├── taiga-subtitles
    │   ├── test.txt
    │   ├── train.txt
    │   └── valid.txt
    ├── test.txt
    ├── train.txt
    └── valid.txt

Note: the test and valid sets have approximately equal amount of subtitles,
news and literature, while the train parts has more literature.

Full statistics::

    $ ./main.py corpora/ out-balanced

    Reading corpora/Subtitles.tar.gz (taiga-subtitles)

    7817 texts, 342 groups in all:
    chars: mean: 22345.2 | min: 8 | median: 22215 | 95%: 34811 | 99%: 44343 | max: 71983 | sum: 174,672,464
    words: mean: 3152.9 | min: 1 | median: 3112 | 95%: 4984 | 99%: 6368 | max: 9803 | sum: 24,646,253
    lines: mean: 575.4 | min: 1 | median: 589 | 95%: 855 | 99%: 1034 | max: 2056 | sum: 4,497,811

    7159 texts, 321 groups in train:
    chars: mean: 22452.2 | min: 8 | median: 22244 | 95%: 35083 | 99%: 44701 | max: 71983 | sum: 160,735,631
    words: mean: 3167.8 | min: 1 | median: 3113 | 95%: 5021 | 99%: 6437 | max: 9803 | sum: 22,678,113
    lines: mean: 576.9 | min: 1 | median: 590 | 95%: 860 | 99%: 1053 | max: 2056 | sum: 4,130,170

    392 texts, 12 groups in valid:
    chars: mean: 18675.2 | min: 17 | median: 20387.5 | 95%: 26615 | 99%: 33343 | max: 38601 | sum: 7,320,676
    words: mean: 2636.0 | min: 2 | median: 2905.5 | 95%: 3836 | 99%: 4713 | max: 5592 | sum: 1,033,297
    lines: mean: 508.0 | min: 1 | median: 513.0 | 95%: 795 | 99%: 910 | max: 942 | sum: 199,154

    266 texts, 9 groups in test:
    chars: mean: 24872.8 | min: 5641 | median: 25213.5 | 95%: 33476 | 99%: 36215 | max: 44295 | sum: 6,616,157
    words: mean: 3514.4 | min: 776 | median: 3573.5 | 95%: 4911 | 99%: 5355 | max: 6662 | sum: 934,843
    lines: mean: 633.4 | min: 172 | median: 639.0 | 95%: 805 | 99%: 860 | max: 935 | sum: 168,487

    Reading corpora/news.zip (taiga-news)

    470304 texts, 470304 groups in all:
    chars: mean: 1256.8 | min: 1 | median: 889.0 | 95%: 3398 | 99%: 7825 | max: 767658 | sum: 591,056,359
    words: mean: 176.3 | min: 1 | median: 127.0 | 95%: 461 | 99%: 1067 | max: 92659 | sum: 82,932,266
    lines: mean: 11.0 | min: 1 | median: 7.0 | 95%: 28 | 99%: 61 | max: 3581 | sum: 5,180,437

    464751 texts, 464751 groups in train:
    chars: mean: 1256.9 | min: 1 | median: 889 | 95%: 3399 | 99%: 7826 | max: 767658 | sum: 584,136,668
    words: mean: 176.3 | min: 1 | median: 127 | 95%: 461 | 99%: 1067 | max: 92659 | sum: 81,958,677
    lines: mean: 11.0 | min: 1 | median: 7 | 95%: 28 | 99%: 61 | max: 3581 | sum: 5,119,590

    2759 texts, 2759 groups in valid:
    chars: mean: 1254.4 | min: 2 | median: 901 | 95%: 3420 | 99%: 8069 | max: 20460 | sum: 3,460,814
    words: mean: 176.5 | min: 1 | median: 128 | 95%: 471 | 99%: 1064 | max: 2837 | sum: 486,921
    lines: mean: 10.8 | min: 1 | median: 7 | 95%: 26 | 99%: 60 | max: 363 | sum: 29,917

    2794 texts, 2794 groups in test:
    chars: mean: 1238.0 | min: 1 | median: 884.0 | 95%: 3233 | 99%: 7692 | max: 26092 | sum: 3,458,877
    words: mean: 174.2 | min: 1 | median: 129.0 | 95%: 440 | 99%: 1048 | max: 3705 | sum: 486,668
    lines: mean: 11.1 | min: 1 | median: 8.0 | 95%: 28 | 99%: 52 | max: 206 | sum: 30,930

    Reading corpora/ruscorpora.tar.gz (rnc-main)

    110708 texts, 110708 groups in all:
    chars: mean: 16144.6 | min: 25 | median: 2524.0 | 95%: 40273 | 99%: 362741 | max: 2145740 | sum: 1,787,341,033
    words: mean: 2341.4 | min: 1 | median: 338.0 | 95%: 5757 | 99%: 53861 | max: 320999 | sum: 259,211,752
    lines: mean: 83.3 | min: 1 | median: 14.0 | 95%: 221 | 99%: 1718 | max: 27511 | sum: 9,226,986

    109960 texts, 109960 groups in train:
    chars: mean: 16126.4 | min: 25 | median: 2524.0 | 95%: 40256 | 99%: 361952 | max: 2145740 | sum: 1,773,257,209
    words: mean: 2338.6 | min: 1 | median: 338.0 | 95%: 5749 | 99%: 53669 | max: 320999 | sum: 257,154,388
    lines: mean: 83.2 | min: 1 | median: 14.0 | 95%: 221 | 99%: 1714 | max: 27511 | sum: 9,147,453

    357 texts, 357 groups in valid:
    chars: mean: 20075.2 | min: 123 | median: 2472 | 95%: 65422 | 99%: 517524 | max: 1043459 | sum: 7,166,843
    words: mean: 2924.3 | min: 15 | median: 323 | 95%: 9254 | 99%: 77450 | max: 157078 | sum: 1,043,983
    lines: mean: 101.2 | min: 2 | median: 14 | 95%: 316 | 99%: 1786 | max: 5434 | sum: 36,121

    391 texts, 391 groups in test:
    chars: mean: 17690.5 | min: 111 | median: 2563 | 95%: 45072 | 99%: 499896 | max: 873864 | sum: 6,916,981
    words: mean: 2591.8 | min: 13 | median: 343 | 95%: 6785 | 99%: 78046 | max: 128698 | sum: 1,013,381
    lines: mean: 111.0 | min: 2 | median: 15 | 95%: 286 | 99%: 2591 | max: 7985 | sum: 43,412

    Reading corpora/ruscorpora.tar.gz (rnc-paper)

    433376 texts, 433376 groups in all:
    chars: mean: 3746.7 | min: 6 | median: 3002.0 | 95%: 8699 | 99%: 14743 | max: 348342 | sum: 1,623,719,443
    words: mean: 519.4 | min: 1 | median: 412.0 | 95%: 1235 | 99%: 2113 | max: 48466 | sum: 225,113,300
    lines: mean: 14.9 | min: 1 | median: 9.0 | 95%: 43 | 99%: 91 | max: 4141 | sum: 6,478,797

    431547 texts, 431547 groups in train:
    chars: mean: 3746.7 | min: 6 | median: 3002 | 95%: 8700 | 99%: 14743 | max: 348342 | sum: 1,616,866,551
    words: mean: 519.4 | min: 1 | median: 412 | 95%: 1235 | 99%: 2112 | max: 48466 | sum: 224,167,044
    lines: mean: 14.9 | min: 1 | median: 9 | 95%: 43 | 99%: 91 | max: 4141 | sum: 6,450,425

    901 texts, 901 groups in valid:
    chars: mean: 3721.4 | min: 36 | median: 3052 | 95%: 8334 | 99%: 15279 | max: 31579 | sum: 3,352,980
    words: mean: 515.9 | min: 5 | median: 414 | 95%: 1210 | 99%: 2206 | max: 3904 | sum: 464,851
    lines: mean: 15.3 | min: 1 | median: 10 | 95%: 42 | 99%: 98 | max: 285 | sum: 13,829

    928 texts, 928 groups in test:
    chars: mean: 3771.5 | min: 22 | median: 2996.0 | 95%: 8336 | 99%: 14303 | max: 62083 | sum: 3,499,912
    words: mean: 518.8 | min: 3 | median: 413.0 | 95%: 1207 | 99%: 2105 | max: 7854 | sum: 481,405
    lines: mean: 15.7 | min: 1 | median: 9.0 | 95%: 45 | 99%: 105 | max: 491 | sum: 14,543

    Reading corpora/ruwiki (ruwiki)

    1451587 texts, 1451587 groups in all:
    chars: mean: 2300.0 | min: 77 | 1%: 128 | 5%: 224 | median: 1147 | 95%: 7567 | 99%: 19596 | max: 430600 | sum: 3,338,636,452
    words: mean: 315.8 | min: 4 | 1%: 17 | 5%: 30 | median: 158 | 95%: 1035 | 99%: 2679 | max: 55739 | sum: 458,355,737
    lines: mean: 17.4 | min: 2 | 1%: 4 | 5%: 4 | median: 12 | 95%: 46 | 99%: 100 | max: 2866 | sum: 25,186,286

    1447729 texts, 1447729 groups in train:
    chars: mean: 2299.4 | min: 77 | 1%: 128 | 5%: 224 | median: 1147 | 95%: 7565 | 99%: 19576 | max: 430600 | sum: 3,328,875,401
    words: mean: 315.7 | min: 4 | 1%: 17 | 5%: 30 | median: 158 | 95%: 1035 | 99%: 2678 | max: 55739 | sum: 457,020,952
    lines: mean: 17.3 | min: 2 | 1%: 4 | 5%: 4 | median: 12 | 95%: 46 | 99%: 100 | max: 2866 | sum: 25,116,486

    1951 texts, 1951 groups in valid:
    chars: mean: 2562.5 | min: 103 | 1%: 137 | 5%: 234 | median: 1155 | 95%: 8236 | 99%: 25811 | max: 131951 | sum: 4,999,481
    words: mean: 350.4 | min: 10 | 1%: 18 | 5%: 32 | median: 161 | 95%: 1148 | 99%: 3524 | max: 17297 | sum: 683,605
    lines: mean: 18.1 | min: 4 | 1%: 4 | 5%: 4 | median: 12 | 95%: 50 | 99%: 111 | max: 551 | sum: 35,386

    1907 texts, 1907 groups in test:
    chars: mean: 2496.9 | min: 103 | 1%: 128 | 5%: 231 | median: 1118 | 95%: 8317 | 99%: 26431 | max: 82053 | sum: 4,761,570
    words: mean: 341.5 | min: 10 | 1%: 17 | 5%: 31 | median: 155 | 95%: 1162 | 99%: 3683 | max: 10076 | sum: 651,180
    lines: mean: 18.0 | min: 4 | 1%: 4 | 5%: 4 | median: 12 | 95%: 48 | 99%: 121 | max: 323 | sum: 34,414

And resulting sizes::

    rnc-main:
    total 3.1G
     12M test.txt
    3.0G train.txt
     13M valid.txt

    rnc-paper:
    total 2.8G
    6.1M test.txt
    2.8G train.txt
    5.8M valid.txt

    taiga-news:
    total 1018M
     6.0M test.txt
    1006M train.txt
     6.0M valid.txt

    taiga-subtitles:
    total 295M
     12M test.txt
    272M train.txt
     13M valid.txt

    ruwiki:
    total 9.0G
     14M test
     15M valid
    9.0G train

Examples from the corpora (full output not shown,
ellipsis at the end added manually)::

    $ head out-balanced/rnc-main/train.txt
    Псина


    У него был блокнот. Толстый такой блокнот с синей обложкой. Ну, вы знаете, эти блокноты — их еще называют «ежедневники». В них есть разделы «кому  позвонить», «что сделать» и «для заметок». В общем,  у него был блокнот. ...
    ...

    $ head out-balanced/rnc-paper/train.txt
    Газета "Ведомости" подала в Арбитражный суд Москвы иск к компании "РБК Информационные системы" за нарушение авторских прав. РБК же в ответ предложило акционерам газеты купить ее у них.
    Российские СМИ нередко обвиняют друг друга в нарушении авторских прав. Они даже пытались создать корпоративный орган, решающий такого рода конфликты. Однако это - первый случай, когда скандал о нарушении авторских прав одного издания в отношении другого развивается публично.
    ...

    $ head out-balanced/taiga-news/train.txt
    Госдепартамент США разрешил въезд в страну обладателям действительных виз, ранее попавших под иммиграционный указ президента США Дональда Трампа, сообщает Reuters.


            «Мы полностью отменили временное аннулирование виз, — заявила пресс-служба Госдепа. —Те лица, визы которых не были физически аннулированы и в настоящее время действительны, могут путешествовать (по территории США)».
    ...

    $ head out-balanced/taiga-subtitles/train.txt
    - Привет, пап. - Доброе утро, девочки.
    Жаль, меня не было этим утром, чтобы приготовить вам блинчики, но никак не угадаешь, когда малыш надумает родиться.
    Пап, мы уже знаем, откуда дети берутся.
    ...


Creating corpora with texts in separate files
+++++++++++++++++++++++++++++++++++++++++++++

Use same source corpora, and then run::

    ./main.py ./corpora/ ./out-as-files/ --as-files


Resulting structure: ``copus-name/train|valid|test/hash-part/hash.txt``.

License
-------

License for the code in this repo is MIT. This does not apply to source corpora.
