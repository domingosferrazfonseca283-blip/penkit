@echo off
title PenKit v2.0
python --version >nul 2>&1 || (echo Python nao encontrado. Instala em python.org & pause & exit)
pip install rich psutil --quiet
python penkit.py
pause
