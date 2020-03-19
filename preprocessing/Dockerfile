FROM python:3.7.5
WORKDIR /usr/src/app

EXPOSE 5000

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./main.py", "server" ]