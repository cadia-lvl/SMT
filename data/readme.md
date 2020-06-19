# Data / Gögn
Hér er lýst gagnaskipan sem er æskileg fyrir forvinnslu og þjálfun.
Í hverri möppu eru gögn, eða vísun í gögn, sem eru öll unnin á sama hátt.

Gert er ráð fyrir því að orðabækur fylgi með kóða en aðrar málheildir séu aðgengilegar frá LVL.
- `parice` er aðgengilegt á terra:`/data/parice/mideind`
- `rmh` er aðgengilegt á terra:`/data/risamalheild/2018`
- `en_mono` er aðgengilegt á terra:`/data/mt_en_mono`

Skjöl sem innihalda íslensk gögn enda á `.is`, `.en` fyrir ensku.
- `raw` inniheldur ýmsar óunnar málheildir og önnur gögn.
  - `dictionary` inniheldur `.tsv` skjöl sem hægt er að nota til að auka og sérsníða orðaforða fyrir kerfi. Öll skjölin eru lesin.
  Þessi gögn eru líka notuð til þess að þjálfa Truecasing líkan, svo huga þarf að réttum há- og lágstöfum í gögnunum.
  - `parice` inniheldur síuð ParIce gögn (þjálfunar og prófunar) frá Miðeind. Snið: Ein setning í línu. Íslenskar setningar í einni skrá sem endar á `.is` og `.en` fyrir enskur.
  - `rmh` inniheldur Risamálheildina í tveimur möppum `CC_BY` og `MIM`, afpakkaðar. Snið: Eins og risamálheild er gefin út; `tei` snið geymt sem `.xml`. 
  - `en_mono` inniheldur enskar málheildir. Sjá `preprocessing` fyrir vinnslu á enskum málheildum.
- `formatted` inniheldur sömu málheildir (`dictionary`, `parice` og `mono`) eftir stöðlun og hreinsun.
- `out` inniheldur tilbúin gögn eftir skiptingu í `train`, `dev` og `test`. `test` er búið til út frá forsíuðum gögnum frá Miðeind.