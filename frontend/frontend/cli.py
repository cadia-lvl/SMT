from typing import Tuple, List
from pathlib import Path

import click

import frontend.api as api
import frontend.bulk as b
import frontend.core as c


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
    return b.tmx_split(paths, src_lang, tar_lang)


@cli.command()
@click.argument('sent')
@click.argument('lang', default='is', type=str)
@click.argument('version', default='v2', type=str)
def sent_preprocess(sent: str, lang: str, version: str) -> str:
    """ # noqa: D205
    Applies the same preprocessing steps to a sentence as specified by the version.
    See api.py for preprocessing step details.
    """
    l_lang = c.Lang(lang)
    sent = api.preprocess(sent, l_lang, version)
    click.echo(sent)
    return sent


if __name__ == '__main__':
    cli()
