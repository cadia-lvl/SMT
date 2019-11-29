FROM python:3.7.5
MAINTAINER haukurpalljonsson@gmail.com

ARG FRONTEND_VERSION="v2.0.0"
EXPOSE 5000

# Add the environment
COPY requirements.txt /opt/

RUN pip install --no-cache-dir -r /opt/requirements.txt && \
    pip install git+https://github.com/cadia-lvl/SMT.git@${FRONTEND_VERSION}#egg=frontend\&subdirectory=frontend && \
    python -c "import nltk;nltk.download('punkt')"
