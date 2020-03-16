from time import time
from collections import defaultdict
from typing import Dict, Callable, Tuple, Set, Generator
import logging
import itertools

import requests
# nltk.download('wordnet')
# nltk.download('averaged_perceptron_tagger')
from nltk.corpus import wordnet as wn
from nltk.stem.wordnet import WordNetLemmatizer
from nltk import pos_tag
from sacremoses import MosesTokenizer, MosesTruecaser, MosesDetokenizer, MosesDetruecaser
import tokenizer as mideind_tok

from .types import (Lang, Tokens, POS, Lemma,
                    iTokCorpus, iCorpus, iEnrichedCorpus,
                    Corpus, EnrichedCorpus)
from preprocessing import file_handler

log = logging.getLogger()

tag_map: Dict[str, str] = defaultdict(lambda: wn.NOUN)
tag_map['J'] = wn.ADJ
tag_map['V'] = wn.VERB
tag_map['R'] = wn.ADV
URL = 'http://malvinnsla.arnastofnun.is'


def get_index_of_segment(segment):
    if segment == 'form':
        return 0
    elif segment == 'pos':
        return 1
    else:
        return 2


def _get_other_indices(segment):
    if segment == 'form':
        yield from (1, 2)
    elif segment == 'pos':
        yield from (0, 2)
    else:
        yield from (0, 1)


def _lazy_load_moses_detokenizer():
    global m_detok
    if not m_detok:
        m_detok = MosesDetokenizer(lang='en')
    return m_detok


def enrich(corpus: iCorpus, lang: str, chunksize: int, lines: int) -> iEnrichedCorpus:
    """Enrich the given corpus with POS and lemma.
    English processing is offline.
    Icelandic processing is done via online API.
    """
    log.info(f'Enriching')
    function: Callable[[iCorpus], EnrichedCorpus] = enrich_sentences_en if lang == 'en' else enrich_sentences_is
    for chunk in file_handler.make_batches(corpus, batch_size=chunksize, max_lines=lines):
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


def tokenize(corpus: iCorpus, lang: Lang) -> iTokCorpus:
    if lang == 'en':
        m_tok = MosesTokenizer(lang='en')
        for line in corpus:
            yield m_tok.tokenize(line, escape=False)
    else:
        for line in corpus:
            yield [token for sent in mideind_tok.split_into_sentences(line) for token in sent.split(' ')]


def detokenize(corpus: iCorpus, lang: Lang) -> iCorpus:
    if lang == 'en':
        m_detok = MosesDetokenizer(lang='en')
        return (m_detok.detokenize(line.split(' '), return_str=True, unescape=False) for line in corpus)
    else:
        return (mideind_tok.detokenize(list(mideind_tok.tokenize(line, normalize=False)), normalize=False) for line in corpus)


def deduplicate(corpus: Generator[str, None, None], known: Set[str]) -> Generator[str, None, None]:
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


def train_truecase(corpus: iTokCorpus, save_to: str, threads=1) -> None:
    truecaser = MosesTruecaser()
    truecaser.train([tokens for tokens in corpus], save_to=save_to, possibly_use_first_token=True, processes=threads, progress_bar=True)


def truecase(corpus: iCorpus, load_from: str) -> iCorpus:
    """
    Input needs to be tokenized and provided as a list of sentences.
    """
    truecaser = MosesTruecaser(load_from=load_from)
    for line in corpus:
        yield truecaser.truecase(line, return_str=True)


def detruecase(corpus: iCorpus) -> iCorpus:
    """
    Input needs to be tokenized and provided as a list of sentences.
    """
    detruecaser = MosesDetruecaser()
    for line in corpus:
        yield detruecaser.detruecase(line, return_str=True)
