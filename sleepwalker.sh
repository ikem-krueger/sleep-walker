#!/bin/sh

while true
do
  idle=$(./xidle)

  echo "$idle"

  if [ "$idle" = "2.000000" ]
  then
    break
  fi
done
