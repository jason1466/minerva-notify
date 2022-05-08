#!/bin/bash

while true;
do
	kill $(ps aux | grep 'Python minervous.py' | awk '{print $2}')
	python3 minervous.py
done