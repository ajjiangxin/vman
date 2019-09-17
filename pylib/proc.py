#!/usr/bin/python3


import subprocess

def read_per_line(cmd):
    proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
    while True:
        line = proc.stdout.readline()
        if line:
            yield line.strip().decode()
        else:
            break

def print_per_line(cmd):
    for line in read_per_line(cmd):
        print(line)
