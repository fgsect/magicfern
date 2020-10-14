#!/bin/bash

for user_id in {500..540}

do
  ./fernflower.py $user_id &
done
