from typing import List, Tuple, Dict


Corpus = List[str]
Lang = str
Name = str
langs = ['en', 'is']

TokCorpus = List[List[str]]
PCorpora = Dict[Lang, Corpus]

Tokens = List[str]
POS = List[str]
Lemma = List[str]
EnrichedSentence = Tuple[Tokens, POS, Lemma]
EnrichedCorpus = List[EnrichedSentence]
EnrichedPCorpora = Dict[Lang, EnrichedCorpus]
