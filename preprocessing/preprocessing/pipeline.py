from time import time
from collections import defaultdict
from typing import Dict, Callable, Tuple, Set, Iterable, List
import logging
import re
from concurrent.futures import ProcessPoolExecutor
from functools import partial
import pathlib

import requests
from nltk.corpus import wordnet as wn
from nltk.stem.wordnet import WordNetLemmatizer
from nltk import pos_tag
from sacremoses import MosesTokenizer, MosesTruecaser, MosesDetokenizer, MosesDetruecaser
import tokenizer as mideind_tok
from tqdm import tqdm
import sentencepiece as spm

from preprocessing.types import (Lang, Tokens, POS, Lemma,
                                 iTokCorpus, iCorpus, iEnrichedCorpus,
                                 Corpus, EnrichedCorpus)
from preprocessing import file_handler

log = logging.getLogger()

tag_map: Dict[str, str] = defaultdict(lambda: wn.NOUN)
tag_map['J'] = wn.ADJ
tag_map['V'] = wn.VERB
tag_map['R'] = wn.ADV
URL = 'http://malvinnsla.arnastofnun.is'


lazy_objects: Dict[str, object] = dict()


def _lazy_load_moses_truecaser(load_from):
    global lazy_objects
    if load_from not in lazy_objects:
        lazy_objects[load_from] = MosesTruecaser(load_from=load_from)
    return lazy_objects[load_from]


def _lazy_load_bpe_tokenizer(lang, model=""):
    global lazy_objects
    if f'tok_bpe_{lang}' not in lazy_objects:
        if model == "":
            path = pathlib.Path(__file__).resolve().parent.joinpath('resources').joinpath(f'{lang}-bpe.model')
        else:
            path = pathlib.Path(model)
        sp = spm.SentencePieceProcessor()
        sp.Load(str(path))
        lazy_objects[f'tok_bpe_{lang}'] = sp
    return lazy_objects[f'tok_bpe_{lang}']


def _get_other_indices(segment):
    if segment == 'form':
        yield from (1, 2)
    elif segment == 'pos':
        yield from (0, 2)
    else:
        yield from (0, 1)


def _lazy_load_moses_tokenizer(lang):
    global lazy_objects
    if f'tok_moses_{lang}' not in lazy_objects:
        lazy_objects[f'tok_moses_{lang}'] = MosesTokenizer(lang=lang)
    return lazy_objects[f'tok_moses_{lang}']


def _lazy_load_moses_detokenizer(lang):
    global lazy_objects
    if f'detok_moses_{lang}' not in lazy_objects:
        lazy_objects[f'detok_moses_{lang}'] = MosesDetokenizer(lang=lang)
    return lazy_objects[f'detok_moses_{lang}']


def _lazy_load_kvistur():
    from kvistur.kvistur import Kvistur
    global lazy_objects
    if 'kvistur' not in lazy_objects:
        lazy_objects['kvistur'] = Kvistur(**file_handler.get_kvistur_resources())
    return lazy_objects['kvistur']


def get_index_of_segment(segment):
    if segment == 'form':
        return 0
    elif segment == 'pos':
        return 1
    else:
        return 2


illegal_replace = [
    {
        # u'\u007c' - |
        'pattern': re.compile(r"\u007c"),
        'unicode': "\u007c",
        'repl': re.compile('_pipe_')
    },
    {
        # u'\u003c', u'\u003e' - <, >
        'pattern': re.compile(r"\u003c"),
        'unicode': "\u003c",
        'repl': re.compile('_lt_')
    },
    {
        'pattern': re.compile(r"\u003e"),
        'unicode': "\u003e",
        'repl': re.compile('_gt_')
    },
    {
        # u'\u005b', u'\u005d' - [, ]
        'pattern': re.compile(r"\u005b"),
        'unicode': "\u005b",
        'repl': re.compile('_bo_')
    },
    {
        'pattern': re.compile(r"\u005d"),
        'unicode': "\u005d",
        'repl': re.compile('_bc_')
    }
]


def escape_moses_chars(corpus: iCorpus) -> iCorpus:
    for sent in corpus:
        for keywords in illegal_replace:
            sent = keywords['pattern'].sub(string=sent, repl=keywords['repl'].pattern)
        yield sent


def de_escape_moses_chars(corpus: iCorpus) -> iCorpus:
    for sent in corpus:
        for keywords in illegal_replace:
            sent = keywords['repl'].sub(string=sent, repl=keywords['unicode'])
        yield sent


def enrich(corpus: iCorpus, lang: str, chunksize: int, lines: int) -> iEnrichedCorpus:
    """Enrich the given corpus with POS and lemma.
    English processing is offline.
    Icelandic processing is done via online API.
    """
    log.info(f'Enriching')
    function: Callable[[iCorpus], EnrichedCorpus] = enrich_sentences_en if lang == 'en' else enrich_sentences_is
    for chunk in file_handler.make_batches(corpus, batch_size=chunksize):
        start = time()
        yield from function(chunk)
        end = time()
        log.debug(f"Bulk enrichment took={end - start:.2f}")


def enrich_sentences_is(corpus: iCorpus) -> EnrichedCorpus:
    enriched_sentences = []
    data = {
        'text': "".join(corpus),
        'lemma': 'on'
    }
    log.debug(f'Request data={data}')
    json = requests.post(URL, data=data).json()
    log.debug(f'Response json={json}')
    for paragraph in json['paragraphs']:
        forms: Tokens = []
        poss: POS = []
        lemmas: Lemma = []
        for sentence in paragraph['sentences']:
            for token in sentence:
                forms.append(token['word'])
                poss.append(token['tag'])
                lemmas.append(token['lemma'])
        enriched_sentences.append((forms, poss, lemmas))
    return enriched_sentences


def enrich_sentences_en(corpus: iCorpus) -> EnrichedCorpus:
    lmtzr = WordNetLemmatizer()
    enriched_sentences = []
    for tokens in tokenize(corpus, lang='en'):
        forms: Tokens = []
        poss: POS = []
        lemmas: Lemma = []
        for token, tag in pos_tag(tokens):
            lemma = lmtzr.lemmatize(token, tag_map[tag[0]])
            forms.append(token)
            poss.append(tag)
            lemmas.append(lemma)
        enriched_sentences.append((forms, poss, lemmas))
    return enriched_sentences


def is_tok(line: str, tokenizer: str, model="") -> List[str]:
    if tokenizer is None or tokenizer == "":
        return [token for sent in mideind_tok.split_into_sentences(line) for token in sent.split(' ')]
    elif tokenizer == 'moses':
        return _lazy_load_moses_tokenizer('is').tokenize(line, escape=False)
    elif tokenizer == 'bpe':
        return _lazy_load_bpe_tokenizer('is', model).EncodeAsPieces(line)
    else:
        raise ValueError(f'Unknown tokenizer={tokenizer}')


def en_tok(line, tokenizer: str, model=""):
    if tokenizer is None or tokenizer == "" or tokenizer == 'moses':
        return _lazy_load_moses_tokenizer('en').tokenize(line, escape=False)
    elif tokenizer == 'bpe':
        return _lazy_load_bpe_tokenizer('en', model).EncodeAsPieces(line)
    else:
        raise ValueError(f'Unknown tokenizer={tokenizer}')


def tokenize(corpus: iCorpus, lang: Lang, tokenizer="", model="", threads=1, batch_size=100000, chunksize=10000, progress=True) -> iTokCorpus:
    if lang == 'en':
        f = partial(en_tok, tokenizer=tokenizer, model=model)
    elif lang == 'is':
        f = partial(is_tok, tokenizer=tokenizer, model=model)
    else:
        raise ValueError(f'Unknown language={lang}')

    if threads == 1:
        if progress:
            corpus = tqdm(corpus)
        for line in corpus:
            yield f(line)
    else:
        with ProcessPoolExecutor(max_workers=threads) as worker:
            for chunk in file_handler.make_batches(corpus, batch_size=batch_size):
                chunk = list(chunk)
                results = tqdm(worker.map(f, chunk, chunksize=chunksize), total=len(chunk))
                for result in results:
                    yield result


def detokenize(corpus: iCorpus, lang: Lang, tokenizer=str, model=str, progress=True) -> iCorpus:
    if progress:
        corpus = tqdm(corpus)
    if lang == 'en':
        if tokenizer is None or tokenizer == "" or tokenizer == 'moses':
            return (_lazy_load_moses_detokenizer('en').detokenize(line.split(' '), return_str=True, unescape=False) for line in corpus)
        elif tokenizer == 'bpe':
            # The bpe tokenizer will not remove \n, but the others will. Make BPE remove \n
            return (_lazy_load_bpe_tokenizer('en', model=model).DecodePieces(line.split(' ')).replace('▁', ' ').replace('\n', '') for line in corpus)
        else:
            raise ValueError(f'Unknown tokenizer={tokenizer}')
    elif lang == 'is':
        if tokenizer is None or tokenizer == "":
            return (mideind_tok.detokenize(list(mideind_tok.tokenize(line, normalize=False)), normalize=False) for line in corpus)
        elif tokenizer == 'bpe':
            # The bpe tokenizer will not remove \n, but the others will. Make BPE remove \n
            return (_lazy_load_bpe_tokenizer('is', model=model).DecodePieces(line.split(' ')).replace('▁', ' ').replace('\n', '') for line in corpus)
        elif tokenizer == 'moses':
            return (_lazy_load_moses_detokenizer('is').detokenize(line.split(' '), return_str=True, unescape=False) for line in corpus)
        else:
            raise ValueError(f'Unknown tokenizer={tokenizer}')
    else:
        raise ValueError(f'Unkown language={lang}')


def deduplicate(corpus: iCorpus, known: Set[str]) -> iCorpus:
    total = 0
    removed = 0
    for sent in corpus:
        total += 1
        if sent in known:
            removed += 1
            continue
        else:
            # Danger: side-effect
            known.add(sent)
            yield sent
    log.info(f'Total lines={total}, removed={removed}')


def split(corpus: Corpus, test_size=2000, shuffle=True, seed=42) -> Tuple[Corpus, Corpus]:
    from sklearn.model_selection import train_test_split
    return train_test_split(corpus, shuffle=shuffle, test_size=test_size, random_state=seed)


def train_truecase(corpus: iCorpus, save_to: str, threads=1) -> None:
    truecaser = MosesTruecaser()
    # Testing loading data beforehand.
    data = [line.split(' ') for line in corpus]
    truecaser.train(data, save_to=save_to, possibly_use_first_token=True, processes=threads, progress_bar=True)


def truecase(corpus: iCorpus, load_from: str) -> iCorpus:
    """
    Input needs to be tokenized and provided as a list of sentences.
    """
    truecaser = _lazy_load_moses_truecaser(load_from=load_from)
    for line in corpus:
        yield truecaser.truecase(line, return_str=True)


def detruecase(corpus: iCorpus) -> iCorpus:
    """
    Input needs to be tokenized and provided as a list of sentences.
    """
    detruecaser = MosesDetruecaser()
    for line in corpus:
        yield detruecaser.detruecase(line, return_str=True)


def extract_known_tokens(corpus: iCorpus) -> Set[str]:
    """
    Input needs to be tokenized and provided as a list of sentences.
    """
    return set(tok.strip() for line in corpus for tok in line.split(' ') if (tok is not None and tok != '\n'))


def unknown_tokens(corpus: iCorpus, known: Set[str]) -> Iterable[Set[str]]:
    """
    Input needs to be tokenized and provided as a list of sentences.
    """
    for line in corpus:
        tokens = set(tok.strip() for tok in line.split(' '))
        yield set(tok for tok in tokens if tok not in known)


def preprocess_line(line: str,
                    lang: str,
                    tokenizer: str,
                    truecase_model: str,
                    known_tokens: Set[str],
                    use_kvistur=False) -> str:
    # Tokenize
    # Truecase
    # Put Moses placeholders
    # Find unkown tokens and substitute with binary split
    tokenized = (" ".join(tokens) for tokens in tokenize([line], lang=lang, tokenizer=tokenizer, progress=False))
    truecased = truecase(tokenized, load_from=truecase_model)
    # Now a string
    escaped = list(escape_moses_chars(truecased))[0]
    # If Kvistur is to be used it needs to be available on PYTHONPATH
    # We only use Kvistur on unknown Icelandic tokens, specify known tokens.
    if use_kvistur and known_tokens is not None and len(known_tokens) != 0 and lang == 'is':
        # We go through the unkown tokens in the line, split on white-space since text is tokenized.
        tokens = [tok.strip() for tok in escaped.split(' ')]
        processed_tokens = []
        for token in tokens:
            # If it is not known
            if token not in known_tokens:
                # Either this does nothing, and the token is the same
                # or the token is split s.t. "x_y" -> "x y"
                token = re.sub("_", " ", _lazy_load_kvistur().re_split(token))
            # We only split each token once.
            processed_tokens.append(token)
        return " ".join(processed_tokens)

    else:
        return escaped


def preprocess(corpus: iCorpus, lang: str, tokenizer: str, truecase_model: str, known_tokens: Set[str], threads=1, batch_size=500000, chunksize=10000) -> iCorpus:
    f = partial(preprocess_line, lang=lang, tokenizer=tokenizer, truecase_model=truecase_model, known_tokens=known_tokens)
    if threads == 1:
        for line in tqdm(corpus):
            yield f(line)
    else:
        with ProcessPoolExecutor(max_workers=threads) as worker:
            for chunk in file_handler.make_batches(corpus, batch_size=batch_size):
                chunk = list(chunk)
                results = tqdm(worker.map(f, chunk, chunksize=chunksize), total=len(chunk))
                for result in results:
                    yield result


def postprocess(corpus: Corpus, lang: str, tokenizer: str) -> Corpus:
    # Remove Moses placeholders
    # Detruecase
    # Detokenize
    de_escaped = de_escape_moses_chars((line for line in corpus))
    detruecased = detruecase(de_escaped)
    detokenized = detokenize(detruecased, lang=lang, tokenizer=tokenizer)
    return list(detokenized)
