from typing import Tuple, List
from pathlib import Path
import re

import click

import corpus as c


@click.group()
def cli():
    """ # noqa: D205
    The main entry point of the command line client.

    Other commands are attached to this functions.
    """


class PathParamType(click.ParamType):
    """A type to convert strings from command line to Path."""  # noqa: D203

    def convert(self, value, param, ctx):
        try:
            return Path(value).resolve()
        except TypeError:
            self.fail(
                "expected a path for Path() conversion, got "
                f"{value!r} of type {type(value).__name__}",
                param,
                ctx,
            )
        except ValueError:
            self.fail(f"{value!r} is not a valid path", param, ctx)


PathType = PathParamType()


@cli.command()
@click.argument('paths', nargs=-1, type=PathType)
@click.option('--src_lang', default='EN-GB', type=str)
@click.option('--tar_lang', default='IS-IS', type=str)
def tmx_split(paths: Tuple[Path],
              src_lang: str,
              tar_lang: str) -> List[Tuple[Path, Path]]:
    return c.tmx_split(paths, src_lang, tar_lang)


@cli.command()
@click.argument('sent')
@click.argument('lang', default='is', type=str)
def sent_process_v1(sent: str, lang: str) -> str:
    """ # noqa: D205
    Applies the same preprocessing steps to a sentence as used in
    baseline Moses en-is/is-en MT system.

    1. Lowercase & unicode normalize NFKC.
    2. Tokenize "is" with "pass-through", "en" with "toktok".
    3. Add URI placeholders for URIs and []()<>.
    """
    l_lang: c.Lang = c.Lang(lang)
    sent = c.sent_lowercase_normalize(sent)
    if l_lang == c.Lang.EN:
        sent = c.sent_tokenize(sent, l_lang, method="toktok")
    else:
        sent = c.sent_tokenize(sent, l_lang, method="pass-through")
    # u'\u007c' - |
    pipe_reg = re.compile(r"\u007c")
    # u'\u003c', u'\u003e' - <, >
    lt_reg = re.compile(r"\u003c")
    gt_reg = re.compile(r"\u003e")

    # u'\u005b', u'\u005d' - [, ]
    bracket_open_reg = re.compile(r"\u005b")
    bracket_close_reg = re.compile(r"\u005d")

    # Taken from https://stackoverflow.com/questions/3809401/what-is-a-good-regular-expression-to-match-a-url?noredirect=1&lq=1
    uri_reg = re.compile(
        r"(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)")
    empty_bracets = re.compile(r"[\[\(]\s*[\]\)]")
    regexps = [
        (uri_reg, '@uri@'),
        (empty_bracets, ""),
        (pipe_reg, '@pipe@'),
        (lt_reg, '@lt@'),
        (gt_reg, '@gt@'),
        (bracket_open_reg, '@brac_open@'),
        (bracket_close_reg, '@brac_close@')
    ]
    sent = c.sent_regexp(sent, regexps)
    click.echo(sent)
    return sent


if __name__ == '__main__':
    cli()
