@echo off
cd /d %~dp0
docker-compose build
docker-compose up