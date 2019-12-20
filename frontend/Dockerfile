FROM python:3.7.5
MAINTAINER haukurpalljonsson@gmail.com

ARG FRONTEND_VERSION
EXPOSE 5000

RUN pip install --no-cache-dir git+https://github.com/cadia-lvl/SMT.git@${FRONTEND_VERSION}#egg=frontend\&subdirectory=frontend
