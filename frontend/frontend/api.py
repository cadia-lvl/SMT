"""
The API for preprocessing and translating sentences.

Supports multiple preprocessing version and multiple (Moses) translation endpoints.
"""
from typing import List
import asyncio
import os
import logging
from time import time

from aiohttp import ClientTimeout
from aiohttp_xmlrpc.client import ServerProxy

from . import core as c
from . import definitions as d

log = logging.getLogger('frontend.api')

MODELS = dict()
"""Holds the accepted "model" parameters and the URL to the translation endpoints.
Set using environment variables. To define a model "en-is" with endpoint "http://localhost:8080/RPC2" set:

export MODEL_en_is=http://localhost:8080/RPC2
"""
for key in os.environ:
    if "MODEL" in key:
        MODELS['-'.join(key.split('_')[1:])] = os.environ.get(key)

PREPROCESSING = dict()
"""Holds the preprocessing version for the "model".
Set using environment variables. To set the model "en-is" to use preprocessing version "v2" set:

export PREPROCESSING_en_is=v2
"""
for key in os.environ:
    if "PREPROCESSING" in key:
        PREPROCESSING['-'.join(key.split('_')[1:])] = os.environ.get(key)


def to_lang(lang: str) -> c.Lang:
    """Get the core.Lang enum based on the string identifier. Only "is" and "en" are supported.

    :param lang: The string identifier for the language\n
    :return: The core.Lang if support.
    """
    return c.Lang(lang)


def preprocess(sent: str, lang: c.Lang, version: str) -> str:
    """Applies the same preprocessing steps to a sentence as specified by the version.
    For further details of the differences between version, see the corresponding functions.

    :param sent: The sentence to preprocess.\n
    :param lang: The core.Lang of the sentence.\n
    :param version: "v1" or "v2".\n
    :return: The preprocessed sentence
    """
    if version == "v1":
        # No longer supported.
        pass
    elif version == "v2":
        sent = preprocess_v2(sent, lang)
    elif version == "v3":
        sent = preprocess_v3(sent, lang)
    else:
        raise ValueError(f"Unkown version={version}")
    return sent


def preprocess_v1(sent: str, lang: c.Lang) -> str:
    """
    DEPRICATED

    Applies the same preprocessing steps to a sentence as used in
    baseline Moses en-is/is-en MT system.

    1. Lowercase & unicode normalize NFKC.
    2. Add URI placeholders.
    3. Tokenize "is" with "pass-through", "en" with "toktok".
    4. Fix URI placeholders and add more placeholders []()<>.

    :param sent: The sentence to preprocess.\n
    :param lang: The core.Lang of the sentence.\n
    :return: The preprocessed sentence
    """
    sent = c.lowercase_normalize(sent)
    regexps = [
        d.SUB_URI
    ]
    sent = c.regexp(sent, regexps)
    if lang == c.Lang.EN:
        sent = c.tokenize(sent, lang, method="toktok")
    else:
        sent = c.tokenize(sent, lang, method="pass-through")
    regexps = [
        d.SUB_PIPE,
        d.SUB_LT,
        d.SUB_GT,
        d.SUB_BRACKET_OPEN,
        d.SUB_BRACKET_CLOSE,
        d.SUB_FIX_PLACEHOLDERS
    ]

    sent = c.regexp(sent, regexps)

    return sent


def preprocess_v2(sent: str, lang: c.Lang) -> str:
    """
    Applies the same preprocessing steps to a sentence as used in the improved
    baseline Moses en-is/is-en MT system.

    1. Lowercase & unicode normalize NFKC.
    2. Add improved URI placeholders.
    3. Tokenize "is" with "pass-through", "en" with "moses".
    4. Fix URI placeholders and add more placeholders []()<>.

    :param sent: The sentence to preprocess.\n
    :param lang: The core.Lang of the sentence.\n
    :return: The preprocessed sentence
    """
    sent = c.lowercase_normalize(sent)
    regexps = [
        d.SUB_URI,
        d.SUB_URI_SIMPLE,
    ]
    sent = c.regexp(sent, regexps)
    if lang == c.Lang.EN:
        sent = c.tokenize(sent, lang, method="moses")
    else:
        sent = c.tokenize(sent, lang, method="pass-through")
    regexps = [
        d.SUB_PIPE,
        d.SUB_LT,
        d.SUB_GT,
        d.SUB_BRACKET_OPEN,
        d.SUB_BRACKET_CLOSE,
        d.SUB_FIX_PLACEHOLDERS
    ]
    sent = c.regexp(sent, regexps)

    return sent


def preprocess_v3(sent: str, lang: c.Lang) -> str:
    """
    Applies the same preprocessing steps to a sentence as used in the en-is-v3 and is-en-v3 Moses MT system.

    1. Lowercase & unicode normalize NFKC.
    2. Add URI placeholders.
    3. Tokenize "is" with "shallow", "en" with "moses".
    4. Fix URI placeholders and add more placeholders for []()<>.

    :param sent: The sentence to preprocess.\n
    :param lang: The core.Lang of the sentence.\n
    :return: The preprocessed sentence
    """
    sent = c.lowercase_normalize(sent)
    regexps = [
        d.SUB_URI,
        d.SUB_URI_SIMPLE,
    ]

    sent = c.regexp(sent, regexps)
    if lang == c.Lang.EN:
        sent = c.tokenize(sent, lang, method="moses")
    else:
        sent = c.tokenize(sent, lang, method="shallow")
    regexps = [
        d.SUB_PIPE,
        d.SUB_LT,
        d.SUB_GT,
        d.SUB_BRACKET_OPEN,
        d.SUB_BRACKET_CLOSE,
        d.SUB_FIX_PLACEHOLDERS
    ]

    sent = c.regexp(sent, regexps)

    return sent


def translate_bulk(sentences: List[str], s_lang: c.Lang, model: str) -> List[str]:
    """
    Preprocesses and translates the sentences from source language to target language.
    Uses the endpoint defined by model and preprocessing steps for the model.

    :param sentences: A list of sentences to translate.\n
    :param s_lang: The source language.\n
    :param model: A string specifying the model. Needs to exist in MODELS.\n
    :return: The translated sentences.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    log.info(f"Defined models={MODELS}")
    log.info(f"Defined preprocessing={PREPROCESSING}")

    async def run():
        translated = []
        client = ServerProxy(MODELS[model], loop=loop, encoding='utf-8', timeout=ClientTimeout(total=60))
        start = time()

        try:
            tasks = [asyncio.create_task(translate(sentence, s_lang, client, PREPROCESSING[model])) for sentence in sentences]
            translated = await asyncio.gather(*tasks)
        except asyncio.TimeoutError as e:
            log.error(f"Translation timed-out", e)

        end = time()
        log.info(f"Bulk translation took={end-start:.2f}\nTranslated: {sentences} -> {translated}")
        await client.close()
        return translated

    translated = loop.run_until_complete(run())
    loop.close()
    return translated


async def translate(sent: str, s_lang: c.Lang, proxy: ServerProxy, version: str) -> str:
    """
    Preprocesses and translates the sentence from source language to target language.
    Uses the endpoint defined by model and preprocessing steps for the model.

    :param sent: The sentence to translate.\n
    :param s_lang: The source language.\n
    :param proxy: An XMLRPC proxy.\n
    :param version: The preprocessing version\n
    :return: The translated sentence.
    """
    log.info(f"Translating: sent={sent}, s_lang={s_lang}, version={version}")
    start = time()

    sentence = preprocess(sent, s_lang, version)
    result = await proxy.translate({'text': sentence})

    end = time()
    translated = result['text']
    log.info(f"Single translation took={end-start:.2f}\nTranslated: {sent} -> {translated}")
    return translated
