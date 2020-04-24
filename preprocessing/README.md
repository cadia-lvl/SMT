# Forvinnsla
Hér eru ýmsar skriftur og Python forrit sem er notað til þess að forvinna gögn áður en Moses líkan er þjálfað sem og til þess að keyra sem þjón til að forvinna gögn fyrir þýðingar.

- `preprocessing` inniheldur Python föll sem hægt er að nota í skjáhermi til þess að keyra ýmis skref.
- `scripts` ýmis konar skriftur sem nota Python forritið á gögn.
- `tests` innihalda nokkrar prófanir á Python forriti.
- `main.py` er notað til þess að keyra Python forritið.
- `requirements.txt` inniheldur lista yfir öll nauðsynleg forrit til þess að keyra Python forritið.

Python forritið er yfirleitt notað í gengum `scipts` eða sem þjónn.

## Skref í forvinnslu
Við byrjum með stöðluð gögn, þar sem skjölin enda á `.en` eða `.is` til þess að vísa til tungumáls.
- Enska málheild
- Íslenska málheild
- ParIce

1. Gögn lesin og tilreidd
1. Truecasing líkan þjálfað á einhliða og tvíhliða gögnum
1. Upphaflegu gögn forunnin með `preprocess` falli
1. Gögn fyrir mállíkön undirbúin.

Einnig eru önnur skref, án númers, sem voru notuð til að framkvæma tilfallandi vinnslu.

## Python forrit

`file_handler.py` manages reading and writing data, including Moses format.
`pipeline.py` applies transformations, including enrichment, to the data.
`tools.py` implements truecasing, splitting, enriching and detokenization.
`types.py` implements useful types common during processing.