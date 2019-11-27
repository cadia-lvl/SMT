FROM continuumio/miniconda3:4.7.12
MAINTAINER haukurpalljonsson@gmail.com

ARG FRONTEND_VERSION="v2.0.0"

# Add the environment
COPY environment.yml /opt/

RUN conda env create -f /opt/environment.yml && \
    echo "conda activate jupyter" >> ~/.bashrc && \
    mkdir /project && \
    mkdir /work

# To be sure that the package is installed into the Jupyter environment.
RUN /bin/bash -c "pip install -e git+https://github.com/cadia-lvl/SMT.git@${FRONTEND_VERSION}#egg=frontend\&subdirectory=frontend" && \
    python -c "import nltk;nltk.download('punkt')"
