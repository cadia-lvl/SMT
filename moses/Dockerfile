FROM ubuntu:18.04
MAINTAINER haukurpalljonsson@gmail.com

ENV MOSESDECODER=/opt/moses
ENV MOSESDECODER_TOOLS=/opt/moses_tools

WORKDIR /opt

ENV PACKAGES_NO_REMOVE="python-minimal"
ENV PACKAGES="build-essential \
    git-core \
    pkg-config \
    automake \
    libtool \
    wget \
    zlib1g-dev \
    python-dev \
    libbz2-dev \
    cmake "

RUN apt-get update && apt-get install -q -y ${PACKAGES} ${PACKAGES_NO_REMOVE} \
    && git clone --depth 1 https://github.com/moses-smt/mosesdecoder.git \
    && cd mosesdecoder \
    && make -j4 -f contrib/Makefiles/install-dependencies.gmake PREFIX=/opt \
    && OPT=/opt ./compile.sh --prefix=${MOSESDECODER} --install-scripts \
    && cd - \
    && rm -rf mosesdecoder \
    && git clone --depth 1 https://github.com/moses-smt/mgiza.git \
    && cd mgiza/mgizapp \
    && cmake . \
    && make -j4 \
    && make -j4 install \
    && mkdir -p ${MOSESDECODER_TOOLS} \
    && cp bin/* scripts/merge_alignment.py ${MOSESDECODER_TOOLS} \
    && cd - \
    && rm -rf mgiza \
    && apt-get remove -q -y ${PACKAGES} \
    && apt-get autoremove -q -y
