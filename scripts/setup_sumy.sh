#!/bin/sh

python3.8 -m pip install git+git://github.com/miso-belica/sumy.
python3.8 -m pip install --user -U nltk
python3.8 -c 'import nltk; nltk.download("punkt")'