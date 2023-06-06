#!/bin/bash
#
nohup /usr/bin/python3 /home/jb/soft/dynreact/log.py -bag browser@apiict00.etsii.upm.es -u log@apiict00.etsii.upm.es -p DynReact -w 900 &
sleep 5
nohup /usr/bin/python3 /home/jb/soft/dynreact/browser.py -u browser@apiict00.etsii.upm.es -p DynReact -lag log@apiict00.etsii.upm.es -lhg launcher@apiict00.etsii.upm.es -w 850 &
sleep 5
