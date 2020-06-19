# Skriftur
`environment.sh` skilgreinir kerfisbreytur eins og skjala/möppu staðsetningar, fjölda þráða og minni og fleira.
- Gert er ráð fyrir því að gögn liggja ekki beint undir ./data heldur séu vísanir á önnur drif. Breytið eftir þörfum.

Best er að keyra `end_to_end.sh` skriftuna sem keyrir öll nauðsynleg skref. Best er að lesa hana ef upp koma erfiðleikar.
Skrefin sem eru keyrð eru númeruð frá 1-4 og er hægt að keyra sérstaklega ef þess þarf:
- 1format
- 2preprocess
- 3train
- 4package

Skriftan gerir ráð fyrir því að hafa aðgang að `sbatch` til þess að senda verk fyrir vinnslu. Hægt er að sleppa því, en það mun taka ennþá lengri tíma í keyrslu.

Full keyrsla tekur um 12 tíma með öllu.

# Pökkun
Sjá [4package/README.md](4package/README.md) fyrir pökkunarleiðbeiningar.