from preprocessing import file_handler


def test_read_rmh():
    from glob import glob
    dir = '/work/haukurpj/data/raw/risamalheild/MIM/433/2012/'
    files = [xml_file for xml_file in glob(f'{dir}/**/*.xml', recursive=True) if not (xml_file.endswith('rmh2Hdr.xml') or xml_file.endswith('rmh1Hdr.xml'))]
    for xml_file in files:
        assert 'Hdr' not in xml_file
    corpus = file_handler.rmh_2_corpus(files[:2], threads=1, chunksize=1)
    assert len(corpus) == 9