#!/usr/bin/python3


import subprocess
import pickle
import os
import sys

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


def fork_and_run(inputs, c_do_per_input, p_do_per_output, bsize=4096):
    rds = []
    for input in inputs:
        r, w = os.pipe()
        c = os.fork()
        if c:
            rds.append(r)
        else:
            output = c_do_per_input(input)
            os.write(w, pickle.dumps(output))
            os.close(w)
            sys.exit(0)
    for r in rds:
        output = pickle.loads(os.read(r, bsize))
        p_do_per_output(output)
        os.close(r)