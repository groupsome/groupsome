#!/usr/bin/env bash

if [ "$(uname)" == "Darwin" ]; then
    brew install libtiff libjpeg webp little-cms2      
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
    if [ -f /etc/redhat-release ]; then
  	sudo yum install libtiff-devel libjpeg-devel libzip-devel freetype-devel \
             lcms2-devel libwebp-devel tcl-devel tk-devel webp
    fi
 
    if [ -f /etc/lsb-release ]; then
        sudo apt-get install libtiff5-dev libjpeg8-dev zlib1g-dev \
             libfreetype6-dev liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev python-tk webp
    fi
elif [ "$(expr substr $(uname -s) 1 10)" == "MINGW32_NT" ]; then
   echo "... iwas anderes"
fi
