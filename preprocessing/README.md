# Preprocessing
A few scripts and classes which are used for preprocessing.

## The pipeline
From a given `(corpus).(en|is)` we transform the parallel corpora to files suitable for Moses and LM training.

1. Read the parallel corpora and transform to `PCorpora` data type.
1. Enrich `PCorpora` with part-of-speech tags and lemmas -> `EnrichedPCorpora`. As an intermediary step, the data is tokenized.
1. Split data to `train/val`, `*/2000` lines.
1. Train a truecasing model for both languages, using `form` and `lemma` parts of the enriched corpus, `truecase-model.(form|lemma).(en|is)`.
1. Write data for Moses and LM training. This will take care of Moses special character requirements.

## The code
`file_handler.py` manages reading and writing data, including Moses format.
`pipeline.py` applies transformations, including enrichment, to the data.
`tools.py` implements truecasing, splitting, enriching and detokenization.
`types.py` implements useful types common during processing.