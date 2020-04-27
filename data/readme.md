# Data / Gögn
Hér er lýst gagnaskipan sem er æskileg fyrir forvinnslu og þjálfun.
Í hverri möppu eru gögn, eða vísun í gögn, sem eru öll unnin á sama hátt.


- `raw` inniheldur ýmsar óunnar málheildir og önnur gögn.
  - `dictionary` inniheldur `.tsv` skjöl sem hægt er að nota til að auka og sérsníða orðaforða fyrir kerfi. Öll skjölin eru lesin.
  Þessi gögn eru líka notuð til þess að þjálfa Truecasing líkan, svo huga þarf að réttum há- og lágstöfum í gögnunum.
  - `parice` inniheldur síuð ParIce gögn (þjálfunar og prófunar) frá Miðeind.
  - `rmh` inniheldur Risamálheildina í tveimur möppum `CC_BY` og `MIM`, afpakkaðar.
  - `en_mono` inniheldur enska málheild.
- `formatted` inniheldur sömu málheildir eftir stöðlun og hreinsun.
- `out` inniheldur tilbúin gögn.

Gert er ráð fyrir því að orðabækur fylgi með kóða en aðrar málheildir séu sóttar frá LVL.
- `parice` er aðgengilegt á terra:`/data/parice/mideind`
- `rmh` er aðgengilegt á terra:`/data/risamalheild/2018`
- `en_mono` er aðgengilegt á terra:`/data/mt_en_mono`

Skjöl sem innihalda íslensk gögn enda á `.is`, `.en` fyrir ensku.