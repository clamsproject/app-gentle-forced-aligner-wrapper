# CLAMS app - Gentle wrapper

This is a CLASM app that wraps [Gentle](https://github.com/lowerquality/gentle). Gentle is a [forced alignment](https://linguistics.berkeley.edu/plab/guestwiki/index.php?title=Forced_alignment) app built on Kaldi. 

## Installation 

### Locally

You need to install Gentle first. Current version of the wrapper is based on Gentle commit [`2148efc`](https://github.com/lowerquality/gentle/tree/2148efccf065aaf86c7c99d89fdbea83d834089d), so it is recommended to use the same version of Gentle for your local installation. Use [`install.sh`](https://github.com/lowerquality/gentle/blob/2148efccf065aaf86c7c99d89fdbea83d834089d/install.sh) from Gentle codebase to first compile Kaldi-based binaries. It will also compile an instance of Kaldi under Gentle directory (`/path/to/gentle/ext/kaldi`), so you need a build toolchain for that. Once compilation (`install.sh`) is done, you should have 
1. `/path/to/gentle/ext/k3` binary 
1. `/path/to/gentle/ext/m3` binary 

(After these are comfirmed, you can delete the Kaldi instance.)

Then you can use [`setup.py`](https://github.com/lowerquality/gentle/blob/2148efccf065aaf86c7c99d89fdbea83d834089d/setup.py) to install a python binding to you local python environment. 
``` bash 
$ cd /path/to/gentle
$ python3 setup.py develop
```

Now it's time to start up the CLAMS wrapper. Install python dependencies in [`requirements.txt`](requirements.txt), and start up `app.py` There are some basic configuration you can use. See help message for details. 

```bash 
$ cd /path/to/gentle-wrapper
$ pip install -r requirements.txt
$ python3 app.py -h 
```


### Using Docker

Build an image using the included [`Dockerfile`](Dockerfile) and run a container. Buliding the image will take fairly long time, as it compiles Kaldi and Gentle from scratch. 


## Usage

The wrapper runs as a HTTP-based web server that uses [MMIF](https://mmif.clams.ai) as input and output format. 