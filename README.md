# Gentle Forced Aligner Wrapper

## Description

This is a CLASM app that wraps [Gentle](https://github.com/lowerquality/gentle). Gentle is a [forced alignment](https://linguistics.berkeley.edu/plab/guestwiki/index.php?title=Forced_alignment) app built on Kaldi. 

## User instruction

General user instructions for CLAMS apps is available at [CLAMS Apps documentation](https://apps.clams.ai/clamsapp).

### System requirements

CLAMS apps are generally recommended to run as a container. Prebuilt container images are available on [CLAMS App Directory](https://apps.clams.ai).

If you want to run this Gentle wrapper locally, you need to install Gentle first. Current version of the wrapper is based on Gentle commit [`f29245a`](https://github.com/lowerquality/gentle/tree/f29245a3645988c6c3bfc5cf3602d60573f4bc9e), so it is recommended to use the same version of Gentle for your local installation. 
Use [`install.sh`](https://github.com/lowerquality/gentle/blob/f29245a3645988c6c3bfc5cf3602d60573f4bc9e/install.sh) from Gentle codebase to first compile Kaldi-based binaries. It will also compile an instance of Kaldi under Gentle directory (`/path/to/gentle/ext/kaldi`), so you need a build toolchain for that. Once compilation (`install.sh`) is done, you should have 
1. `/path/to/gentle/ext/k3` binary 
1. `/path/to/gentle/ext/m3` binary 

(After these are confirmed, you can delete the Kaldi instance.)

Then you can use [`setup.py`](https://github.com/lowerquality/gentle/blob/f29245a3645988c6c3bfc5cf3602d60573f4bc9e/setup.py) to install a python binding to you local python environment. 
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


### Configurable runtime parameter

For the full list of parameters, please refer to the app metadata from [CLAMS App Directory](https://apps.clams.ai/clamsapp/) or [`metadata.py`](metadata.py) file in this repository.

