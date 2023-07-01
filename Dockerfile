FROM clamsproject/clams-python-ffmpeg:0.5.1

LABEL maintainer="CLAMS Team <admin@clams.ai>"
LABEL issues="https://github.com/clamsproject/app-gentle-forced-aligner-wrapper/issues"

RUN apt update 
RUN apt install -y wget unzip git subversion python2.7
RUN apt install -y build-essential zlib1g-dev automake autoconf sox gfortran libtool 

# install gentle
RUN git clone https://github.com/lowerquality/gentle.git /opt/gentle
WORKDIR /opt/gentle
RUN git checkout f29245a
RUN git submodule init
RUN git submodule update
## prep kaldi 
ENV MAKEFLAGS=' -j8'
# RUN git clone https://github.com/kaldi-asr/kaldi /opt/gentle/ext/kaldi
# RUN git --git-dir /opt/gentle/ext/kaldi/.git checkout 7ffc9ddeb3c8436e16aece88364462c89672a183
WORKDIR /opt/gentle/ext/kaldi/tools
RUN make
RUN ./extras/install_openblas.sh
WORKDIR /opt/gentle/ext/kaldi/src
RUN ./configure --static --static-math=yes --static-fst=yes --use-cuda=no --openblas-root=../tools/OpenBLAS/install
RUN make depend
## build graph binaries that's actually used
WORKDIR /opt/gentle/ext
RUN make depend 
RUN make
## removed build residue
RUN rm -rf kaldi *o
## and finally install `gentle` python package 
WORKDIR /opt/gentle
RUN python3 -m pip install incremental twisted
RUN python3 setup.py develop
RUN ./install_models.sh

COPY . /app
WORKDIR /app

# Install python app dependencies
RUN python3 -m pip install -r requirements.txt

CMD ["python3", "app.py", "--production"]
