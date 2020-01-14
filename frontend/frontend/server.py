"""A server front-end to an MT system. A RESTful interface. Implements a translation interface to Moses.
"""
import logging
import uuid

from flask import Flask
from flask_cors import CORS
from flask_restful import Resource, Api, reqparse

from . import api as a

log = logging.getLogger('frontend.server')
app = Flask(__name__)
CORS(app)
api = Api(app)

parser = reqparse.RequestParser()
parser.add_argument('contents',
                    type=list,
                    required=True,
                    location='json',
                    help='The sentence list to translate.')
parser.add_argument('sourceLanguageCode',
                    type=str,
                    required=True,
                    location='json',
                    choices=('en', 'is'),
                    help='The language code of the sentences.', )
parser.add_argument('targetLanguageCode',
                    type=str,
                    required=True,
                    location='json',
                    choices=('en', 'is'),
                    help='The language code to translate to.', )
parser.add_argument('model',
                    type=str,
                    required=True,
                    location='json',
                    choices=a.MODELS,
                    help='The model to use to translate.', )


class Ping(Resource):
    """A dummy resource which responds "pong" if called.

    :param path: / \n
    """
    def get(self):
        """
        :param method: GET\n
        :return 'pong'
        """


class MosesTranslate(Resource):
    """The translation endpoint. Accepts a list of sentences to translate and returns the results.

    :param path: /translateText \n

    """
    def post(self):
        """
        :param method: POST \n
        :param accepts: application/json \n
        :param payload:\n
            {
                "contents": ["Sentence to translate"],
                "sourceLanguageCode": "en"/"is",
                "targetLanguageCode": "en"/"is",
                "model": "The model to use"
            }
        :param returns:\n
            {
                "translations": [
                    {
                        "translatedText": "The translated text",
                        "model": "The model used"
                    }
                ]
            }
        :return:
        """
        args = parser.parse_args(strict=True)
        sentences = args['contents']
        source_lang = a.to_lang(args['sourceLanguageCode'])
        target_lang = a.to_lang(args['targetLanguageCode'])
        model = args['model']
        id = uuid.uuid4().hex
        log.info(f"""Received translation request id={id}:
    contents={sentences}
    sourceLanguageCode={source_lang}
    targetLanguageCode={target_lang}
    model={model}""")
        # We construct the model string so it fits what the api expects.
        model = "-".join([source_lang, target_lang, model])
        log.info(f"Parsed model string to model={model}")
        translated_sentences = a.translate_bulk(sentences, source_lang, target_lang, model, id)
        log.info(f"Sending translation response id={id}")

        return {
            "translations": [
                {
                    'translatedText': translation,
                    'model': model
                }
                for translation in translated_sentences
            ]
        }


api.add_resource(Ping, '/')
api.add_resource(MosesTranslate, '/translateText')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
