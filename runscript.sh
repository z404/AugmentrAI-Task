#!/bin/bash
rasa train
rasa run --enable-api -p 80 &
rasa run actions