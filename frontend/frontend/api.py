"""
Moses MT API. To be used by MT clients (server.py).
"""
from typing import List, Generator
import asyncio

from aiohttp_xmlrpc.client import ServerProxy

import frontend.core as c

# TODO: Put in config file
MODELS = {
    'baseline': 'http://localhost/RPC2'
}
PROCESSING = {
    'baseline': 'v1'
}


def to_lang(lang: str) -> c.Lang:
    if lang == 'is':
        return c.Lang.IS
    elif lang == 'en':
        return c.Lang.EN
    raise ValueError("Invalid language specified. Only 'is' and 'en' allowed.")


def preprocess(sent: str, lang: c.Lang, version: str) -> str:
    """ # noqa: D205
    Applies the same preprocessing steps to a sentence as specified by the version.

    :param sent: The sentence to preprocess.
    :param lang: The Lang of the sentence, frontend.Lang.IS or frontend.Lang.EN.
    :param version: "v1" for  or "v2"
    :return: The preprocessed sentence

    v1: baseline Moses en-is/is-en MT system.
    1. Lowercase & unicode normalize NFKC.
    2. Tokenize "is" with "pass-through", "en" with "toktok".
    3. Add URI placeholders for URIs and []()<>.

    v2: Improved baseline Moses en-is/is-en MT system.
    1. Lowercase & unicode normalize NFKC.
    2. Tokenize "is" with "pass-through", "en" with "Dockerfile".
    3. Add URI placeholders for URIs and []()<>.
    """
    if version == "v1":
        sent = preprocess_v1(sent, lang)
    elif version == "v2":
        sent = preprocess_v2(sent, lang)
    return sent


def preprocess_v1(sent: str, lang: c.Lang) -> str:
    """ # noqa: D205
    Applies the same preprocessing steps to a sentence as used in
    baseline Moses en-is/is-en MT system.

    1. Lowercase & unicode normalize NFKC.
    2. Add URI placeholders.
    3. Tokenize "is" with "pass-through", "en" with "toktok".
    4. Fix URI placeholders and add more placeholders []()<>.
    """
    sent = c.lowercase_normalize(sent)
    regexps = [
        c.REGEXP_SUB['URI'],
        c.REGEXP_SUB['EMPTY-BRACKETS']
    ]
    sent = c.regexp(sent, regexps)
    if lang == c.Lang.EN:
        sent = c.tokenize(sent, lang, method="toktok")
    else:
        sent = c.tokenize(sent, lang, method="pass-through")
    regexps = [
        c.REGEXP_SUB['PIPE'],
        c.REGEXP_SUB['FIX-URI'],
        c.REGEXP_SUB['LT'],
        c.REGEXP_SUB['GT'],
        c.REGEXP_SUB['BRACKET-OPEN'],
        c.REGEXP_SUB['BRACKET-CLOSE']
    ]
    sent = c.regexp(sent, regexps)

    return sent


def preprocess_v2(sent: str, lang: c.Lang) -> str:
    """ # noqa: D205
    Applies the same preprocessing steps to a sentence as used in the improved
    baseline Moses en-is/is-en MT system.

    1. Lowercase & unicode normalize NFKC.
    2. Add imporoved URI placeholders.
    3. Tokenize "is" with "pass-through", "en" with "Dockerfile".
    4. Fix URI placeholders and add more placeholders []()<>.
    """
    sent = c.lowercase_normalize(sent)
    regexps = [
        c.REGEXP_SUB['URI'],
        c.REGEXP_SUB['URI-SIMPLE'],
        c.REGEXP_SUB['EMPTY-BRACKETS']
    ]
    sent = c.regexp(sent, regexps)
    if lang == c.Lang.EN:
        sent = c.tokenize(sent, lang, method="Dockerfile")
    else:
        sent = c.tokenize(sent, lang, method="pass-through")
    regexps = [
        c.REGEXP_SUB['PIPE'],
        c.REGEXP_SUB['FIX-URI'],
        c.REGEXP_SUB['LT'],
        c.REGEXP_SUB['GT'],
        c.REGEXP_SUB['BRACKET-OPEN'],
        c.REGEXP_SUB['BRACKET-CLOSE']
    ]
    sent = c.regexp(sent, regexps)

    return sent


def translate_bulk(sentences: List[str], s_lang: c.Lang, model: str) -> List[str]:
    """
    Translates the sentences from source language to target language.
    :param model: A string specifying the model.
    :param sentences: The sentences to translate.
    :param s_lang: The source language.
    :return: The translated sentence.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    translated = []

    async def run():
        client = ServerProxy(MODELS[model], loop=loop, encoding='utf-8')
        for sentence in sentences:
            translated.append(await translate(sentence, s_lang, client, PROCESSING[model]))
        await client.close()

    loop.run_until_complete(run())
    return translated


async def translate(sent: str, s_lang: c.Lang, proxy: ServerProxy, version: str) -> Generator[str, None, None]:
    """
    Translates the sentence from source language to target language.
    :param proxy: An XMLRPC proxy.
    :param version: The preprocessing version
    :param sent: The sentence to translate.
    :param s_lang: The source language.
    :return: The translated sentence.
    """
    sentence = preprocess(sent, s_lang, version)
    result = await proxy.translate({'text': sentence})
    return result['text']
