# Use the same base image version as the clams-python python library version
FROM ghcr.io/clamsproject/clams-python-ffmpeg:1.0.9
# See https://github.com/orgs/clamsproject/packages?tab=packages&q=clams-python for more base images
# IF you want to automatically publish this image to the clamsproject organization, 
# 1. you should have generated this template without --no-github-actions flag
# 1. to add arm64 support, change relevant line in .github/workflows/container.yml 
#     * NOTE that a lots of software doesn't install/compile or run on arm64 architecture out of the box 
#     * make sure you locally test the compatibility of all software dependencies before using arm64 support 
# 1. use a git tag to trigger the github action. You need to use git tag to properly set app version anyway

################################################################################
# DO NOT EDIT THIS SECTION
ARG CLAMS_APP_VERSION
ENV CLAMS_APP_VERSION ${CLAMS_APP_VERSION}
################################################################################

################################################################################
# clams-python base images are based on debian distro
# install more system packages as needed using the apt manager
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
################################################################################

################################################################################
# main app installation
COPY ./ /app
WORKDIR /app
RUN pip3 install -r requirements.txt

# default command to run the CLAMS app in a production server 
CMD ["python3", "app.py", "--production"]
################################################################################
