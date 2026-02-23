#!/bin/bash
export WORKDIR="$PWD"
export PATH=$HOME/micromamba/bin:$PATH
export MAMBA_ROOT_PREFIX=$HOME/micromamba
eval "$(micromamba shell hook -s zsh)"
micromamba activate Nano
