FROM ubuntu:19.04

RUN apt-get update && \
    apt-get install -y git python3 python3-pip python3-setuptools

RUN apt-get install -y ffmpeg
RUN apt-get install -y gfortran libblas-dev liblapack-dev python2.7
RUN git clone https://github.com/lowerquality/gentle.git /opt/gentle
WORKDIR /opt/gentle
RUN git submodule init && git submodule update
RUN bash install_deps.sh
WORKDIR /opt/gentle/ext/kaldi/tools
RUN make clean  || echo ""
RUN make
RUN bash ./extras/install_openblas.sh
WORKDIR /opt/gentle/ext/kaldi/src
RUN make clean || echo ""
RUN ./configure --static --static-math=yes --static-fst=yes --use-cuda=no --openblas-root=../tools/OpenBLAS/install
RUN make depend

WORKDIR /opt/gentle
RUN bash install_models.sh
WORKDIR /opt/gentle/ext
RUN make depend && make

COPY ./ ./app
WORKDIR ./app
RUN pip install -r requirements.txt


ENTRYPOINT ["python"]
CMD ["app.py"]
