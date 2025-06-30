@echo off
cd /d %~dp0
powershell -ExecutionPolicy Bypass -File "hello.ps1"
pause
