#!/bin/bash

docker run -it --rm \
  -v $(PWD):/halftone \
  -w="/halftone" \
  yoanlin/opencv-python3 \
  python3 halftoner.py $@