#!/bin/bash
command -v python3 &>/dev/null || (echo Python3 nao encontrado && exit 1)
pip3 install rich psutil --quiet
python3 penkit.py
