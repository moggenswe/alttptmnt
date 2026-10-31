@echo off
rem Double-click: create a seed, start, check and stop a session (see tools\menu.ps1).
title TMNT x A Link to the Past
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\menu.ps1"
