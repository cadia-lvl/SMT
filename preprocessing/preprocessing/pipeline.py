from time import time
from collections import defaultdict
from typing import Dict, Callable, Union, Tuple
import logging

import requests
# nltk.download('wordnet')
# nltk.download('averaged_perceptron_tagger')
from nltk.corpus import wordnet as wn
from nltk.stem.wordnet import WordNetLemmatizer
from nltk import pos_tag
from sacremoses import MosesTokenizer, MosesTruecaser

from .types import (Lang, Tokens, POS, Lemma,
                    TokCorpus,
                    PCorpora, EnrichedPCorpora,
                    Corpus, EnrichedCorpus)


log = logging.getLogger()

tag_map: Dict[str, str] = defaultdict(lambda: wn.NOUN)
tag_map['J'] = wn.ADJ
tag_map['V'] = wn.VERB
tag_map['R'] = wn.ADV
URL = 'http://malvinnsla.arnastofnun.is'

m_tok = None


def _lazy_load_moses_tokenizer():
    global m_tok
    if not m_tok:
        m_tok = MosesTokenizer(lang='en')
    return m_tok


def _make_chunks(sentences, chunksize: int, max_lines: int):
    length = len(sentences)
    if max_lines:
        length = min(length, max_lines)
    for i in range(0, len(sentences), chunksize):
        yield sentences[i:i + chunksize]


def enrich_p_corpora(p_corpora: PCorpora, chunksize, lines: int) -> EnrichedPCorpora:
    """Enrich the given corpus with POS and lemma.
    English processing is offline.
    Icelandic processing is done via online API.
    """
    enriched_p_corpora: Dict[Lang, EnrichedCorpus] = dict()
    for lang in p_corpora:
        log.info(f'Working on lang={lang}')
        enriched_p_corpora[lang] = []
        function: Callable[[Corpus], EnrichedCorpus] = enrich_sentences_en if lang == 'en' else enrich_sentences_is
        for chunk in _make_chunks(p_corpora[lang], chunksize=chunksize, max_lines=lines):
            start = time()
            enriched_p_corpora[lang].extend(function(chunk))
            end = time()
            log.debug(f"Bulk enrichment took={end - start:.2f}")

    return enriched_p_corpora


def enrich_sentences_is(corpus: Corpus) -> EnrichedCorpus:
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


def enrich_sentences_en(corpus: Corpus) -> EnrichedCorpus:
    lmtzr = WordNetLemmatizer()
    enriched_sentences = []
    for sentence in corpus:
        forms: Tokens = []
        poss: POS = []
        lemmas: Lemma = []
        tokens = tokenize(sentence, 'en')
        for token, tag in pos_tag(tokens):
            lemma = lmtzr.lemmatize(token, tag_map[tag[0]])
            forms.append(token)
            poss.append(tag)
            lemmas.append(lemma)
        enriched_sentences.append((forms, poss, lemmas))
    return enriched_sentences


def tokenize(line: str, lang: Lang) -> Tokens:
    if lang == 'en':
        m_tok = _lazy_load_moses_tokenizer()
        return m_tok.tokenize(line, escape=False)
    raise NotImplementedError("Only English tokeniziation")


def split_corpora(corpora: Union[PCorpora, EnrichedPCorpora], test_size=2000, shuffle=True, seed=42) -> Union[Tuple[PCorpora, PCorpora], Tuple[EnrichedPCorpora, EnrichedPCorpora]]:
    from sklearn.model_selection import train_test_split
    train, test = dict(), dict()
    for lang in corpora:
        train[lang], test[lang] = train_test_split(corpora[lang], shuffle=shuffle, test_size=test_size, random_state=seed)
    return train, test


def train_truecase(corpus: TokCorpus, save_to: str, threads=1) -> None:
    truecaser = MosesTruecaser()
    truecaser.train([tokens for tokens in corpus], save_to=save_to, possibly_use_first_token=False, processes=threads, progress_bar=True)


def truecase(corpus: TokCorpus, load_from: str) -> TokCorpus:
    truecaser = MosesTruecaser(load_from=load_from)
    return [[truecaser.truecase(token) for token in tokens] for tokens in corpus]
