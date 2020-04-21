"""
The API for preprocessing and translating sentences.

Supports multiple preprocessing version and multiple (Moses) translation endpoints.
"""
from typing import List
import asyncio
import os
import logging
from time import time
import pathlib

from aiohttp import ClientTimeout
from aiohttp_xmlrpc.client import ServerProxy

from preprocessing import pipeline

log = logging.getLogger('frontend.api')

MODELS = dict()
"""Holds the accepted "model" parameters and the URL to the translation endpoints.
Set using environment variables. To define a model "en-is-baseline" with endpoint "http://localhost:8080/RPC2" set:

export MODEL_en_is_baseline=http://localhost:8080/RPC2
"""
for key in os.environ:
    if "MODEL" in key:
        MODELS['-'.join(key.split('_')[1:])] = os.environ.get(key)

log.info(f'Defined translation models: {MODELS}')

TRUECASERS = dict()
"""Holds the truecasing models paths.
We first load the models from the resources package; {'en':'path'}
Additional models can be set via environment variables or overwritten. To define a truecasing model for "is" with path "/here/it/is" set:

export TRUECASE_is=/here/it/is
"""
for lang in ['en', 'is']:
    path = pathlib.Path(os.path.realpath(__file__)).parent.joinpath('resources').joinpath(f'truecase-model.{lang}')
    if path.exists():
        TRUECASERS[lang] = str(path)
for key in os.environ:
    if "TRUECASE" in key:
        TRUECASERS[key.split('_')[1]] = os.environ.get(key)
log.info(f'Defined truecasing models: {TRUECASERS}')

TOKENS = dict()
"""Holds the known tokens paths, only IS supported in preprocessing. Used for splitting unkown compounds.
We first load from the resources package; {'is':'path'}
Additional models can be set via environment variables or overwritten. To define known tokens for "is" with path "/here/it/is" set:

export TOKENS_is=/here/it/is
"""
for lang in ['is', 'en']:
    path = pathlib.Path(os.path.realpath(__file__)).parent.joinpath('resources').joinpath(f'tok.{lang}')
    if path.exists():
        with path.open() as f_in:
            TOKENS[lang] = set(line.strip() for line in f_in)
    else:
        TOKENS[lang] = set()
for key in os.environ:
    if "TOKENS" in key:
        path = pathlib.Path(os.environ.get(key))
        with path.open() as f_in:
            TOKENS[key.split('_')[1]] = set(line.strip() for line in f_in)
log.info(f'Defined known tokens: {(lang, len(TOKENS[lang])) for lang in TOKENS}')


def preprocess(sent: str, lang: str) -> str:
    """
    Applies the necessary preprocessing steps to a sentence before translation.

    :param sent: The sentence to preprocess.\n
    :param lang: The language of the sentence.\n
    :return: The preprocessed sentence
    """
    try:
        truecase_model = TRUECASERS[lang]
    except KeyError:
        raise ValueError(f'Truecase model not specified for lang={lang}')
    # TODO: Maybe we want to have some known tokens in production
    return pipeline.preprocess_line(sent, lang=lang, truecase_model=truecase_model, known_tokens=TOKENS[lang], tokenizer="")


def postprocess(sent: str, lang: str) -> str:
    """
    Applies the necessary postprocessing steps to a sentence after translation.

    :param sent: The sentence to process.\n
    :param lang: The language of the sentence.\n
    :return: The processed sentence.
    """
    return pipeline.postprocess([sent], lang=lang, tokenizer="")[0]


def translate_bulk(sentences: List[str], s_lang: str, t_lang: str, model: str, id: str) -> List[str]:
    """
    Preprocesses and translates the sentences from source language to target language.
    Uses the endpoint defined by model and preprocessing steps for the model.

    :param sentences: A list of sentences to translate.\n
    :param s_lang: The source language.\n
    :param t_lang: The target language.\n
    :param model: A string specifying the model.\n
    :return: The translated sentences.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    log.info(f"Defined models={MODELS}")

    async def run():
        translated = []
        client = ServerProxy(MODELS[model], loop=loop, encoding='utf-8', timeout=ClientTimeout(total=60))
        start = time()

        try:
            tasks = [asyncio.create_task(translate(sentence, s_lang, t_lang, client, id)) for
                     sentence in sentences]
            translated = await asyncio.gather(*tasks)
        except asyncio.TimeoutError as e:
            log.error(f"Translation timed-out", e)

        end = time()
        log.info(f"Bulk translation id={id}: took={end - start:.2f}")
        await client.close()
        return translated

    translated = loop.run_until_complete(run())
    loop.close()
    return translated


async def translate(sent: str, s_lang: str, t_lang: str, proxy: ServerProxy, id: str) -> str:
    """
    Preprocesses and translates the sentence from source language to target language.
    Uses the endpoint defined by model and preprocessing steps for the model.

    :param sent: The sentence to translate.\n
    :param s_lang: The source language.\n
    :param t_lang: The target language.\n
    :param proxy: An XMLRPC proxy.\n
    :param version: The preprocessing version\n
    :param id: The UUID of the translation request.\n
    :return: The translated sentence.
    """
    log.info(f"Translation id={id}: source={sent}")

    sentence = preprocess(sent, s_lang)
    log.info(f"Translation id={id}: preprocessed={sentence}")

    start = time()
    result = await proxy.translate({'text': sentence})
    end = time()
    log.info(f"Translation id={id}: took={end - start:.2f}")

    translated = result['text']
    log.info(f"Translation id={id}: {sentence} -> {translated}")

    translated = postprocess(translated, t_lang)
    log.info(f"Translation id={id}: postprocessed={translated}")
    return translated
