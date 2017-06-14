#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import signal
import sys
import time

def sigterm_handler(signal, frame):
    # save the state here or do whatever you want
    print('booyah! bye bye')
    
    sys.exit(0)

signal.signal(signal.SIGTERM, sigterm_handler)

def main():
    for i in range(100):
        print(i)
        
        time.sleep(i)

if __name__ == '__main__':
    main()
