#!/bin/bash
/root/miniconda3/bin/python server.py 2>&1 | awk '{ print strftime("[%Y-%m-%d %H:%M:%S] "), $0; fflush() }' >> /var/log/shadowrocket.log
