from typing import List, Tuple, Dict

Sentence = List
POS = List
Lemma = List

Corpus = List[str]
langs = ['en', 'is']

EnrichedSentence = Tuple[Sentence, POS, Lemma]
EnrichedCorpus = List[EnrichedSentence]
ParaCorpora = Dict[str, Dict[str, EnrichedCorpus]]


def path_to_corpus(in_path: str) -> Corpus:
    with open(in_path) as f_in:
        return f_in.readlines()


def read_paracorpora_pickle(path: str) -> ParaCorpora:
    import pickle
    with open(path, 'rb') as handle:
        return pickle.load(handle)
