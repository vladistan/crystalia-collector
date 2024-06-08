#!/usr/bin/env bash

mkdir -p ch1
mkdir -p ch2
mkdir -p ch2/add
mkdir -p ch3

lorem --lorem --line 19 > ch1/ch1a.txt
lorem --lorem --line 25 > ch1/ch1b.txt
lorem --lorem --line 40 > ch1/ch1c.txt

lorem --spook --line 19 > ch2/ch2a.txt
lorem --spook --line 25 > ch2/ch2b.txt
lorem --spook --line 40 > ch2/ch2c.txt
lorem --spook --line 11 > ch2/add/ch2c_a.txt

lorem --strindberg --line 19 > ch3/ch3a.txt
lorem --strindberg --line 25 > ch3/ch3b.txt


