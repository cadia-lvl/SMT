"""
A server front-end to an MT system, RESTful. Implements a translation interface to Moses.

The server is split in two, the RESTful interface (server.py) and a framework agnostic API (api.py).
"""
from flask import Flask
from flask_restful import Resource, Api, reqparse

import frontend.api as a

app = Flask(__name__)
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
    def get(self):
        return 'pong'


class MosesTranslate(Resource):
    def post(self):
        args = parser.parse_args(strict=True)
        sentences = args['contents']
        source_lang = a.to_lang(args['sourceLanguageCode'])
        target_lang = a.to_lang(args['targetLanguageCode'])
        # We do not perform any correctness checks on the model name passed in.
        model = args['model']
        translated_sentences = a.translate_bulk(sentences, source_lang, model)

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
