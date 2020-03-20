FROM python:3.7.5
WORKDIR /usr/src/app

EXPOSE 5000

ENV TRUECASE_en=./resources/truecase-model.en
ENV TRUECASE_is=./resources/truecase-model.is
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    python -c "import nltk; nltk.download('wordnet'); nltk.download('averaged_perceptron_tagger')"

COPY . .

CMD [ "python", "./main.py", "server" ]