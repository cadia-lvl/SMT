from preprocessing.types import iCorpus
from preprocessing import file_handler
import logging

import requests

log = logging.getLogger()


def translate_bulk(sentences: iCorpus, url: str, s_lang: str, t_lang: str, model: str, batch_size=20) -> iCorpus:
    for batch in file_handler.make_batches(sentences, batch_size=batch_size):
        response = requests.post(url=url, json={
            "contents": [line for line in batch],
            "sourceLanguageCode": s_lang,
            "targetLanguageCode": t_lang,
            "model": model
        })
        if not response.ok:
            log.debug(f'Error in response: {response.text}')
        for translation in response.json()['translations']:
            yield translation['translatedText']
