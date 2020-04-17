# Þjálfa Moses líkan
Í þessari skrá eru ýmsar skriftur til þess að þjálfa mismunandi Moses líkön og aðrar skriftur sem koma að Moses þjálfun.

- Skrifturnar vísa í gögn sem verða að vera til staðar.
- Skrifturnar gera ráð fyrir því að Moses og önnur tilheyrandi tól séu uppsett.
- Skrifturnar þjálfa, fínpússa, pakka og meta Moses líkan.

## `run_in_singularity`
Skriftan hjúpar aðrar skriftur með því að keyra þær í gegnum docker/singularity geymi með Moses uppsett.
Það mikilvægasta sem hún gerir er að setja kerfisbreyturnar `MOSESDECODER` og `MOSESDECODER_TOOLS` sem vísa á uppsett Moses og önnur nauðsynleg tól fyrir Moses.

## `lm.sh`
Skriftan þjálfar og pakka KenLM mállíkani og nýtir sér KenLM forrit sem er innbyggt í Moses.

## Aðrar skriftur
Aðrar skriftur eru skilgreiningar á Moses líkönum sem hafa verið þjálfaðar.
