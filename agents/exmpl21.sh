#!/bin/bash
#
nohup /usr/bin/python3 ./log.py -bag browser@apiict03.etsii.upm.es -u log@apiict03.etsii.upm.es -p DynReact -w 900 &
sleep 5
nohup /usr/bin/python3 ./browser.py -u browser@apiict03.etsii.upm.es -p DynReact -lag log@apiict03.etsii.upm.es -lhg launcher@apiict03.etsii.upm.es -w 850 &
sleep 5
#nohup /usr/bin/python3 ./coil.py -w 12000 -v 40 -st 15000 -s on -b 600 -c cO202109105 -o O202109-01 -an 4 -l NWW1 -ph VA09 -ah 900 -os 8 -sg X400 -thk 0.5 -ll 4400 -bag browser@apiict03.etsii.upm.es -lag log@apiict03.etsii.upm.es -u c004@apiict03.etsii.upm.es -p DynReact &
#sleep 5
#nohup /usr/bin/python3 ./coil.py -w 12500 -v 40 -st 15000 -s on -b 600 -c cO202109106 -o O202109-02 -an 5 -l NWW1 -ph VA09 -ah 985 -os 3 -sg X400 -thk 0.3 -ll 4300 -bag browser@apiict03.etsii.upm.es -lag log@apiict03.etsii.upm.es -u c005@apiict03.etsii.upm.es -p DynReact &
#sleep 5
#nohup /usr/bin/python3 ./coil.py -w 12100 -v 40 -st 15000 -s on -b 600 -c cO202109107 -o O202109-01 -an 6 -l NWW3 -ph VA09 -ah 980 -os 3 -sg X400 -thk 0.35 -ll 4200 -bag browser@apiict03.etsii.upm.es -lag log@apiict03.etsii.upm.es -u c006@apiict03.etsii.upm.es -p DynReact &
#sleep 5

nohup /usr/bin/python3 ./launcher.py -oc "O202109-04" -sg "X400" -at 0.6 -wi 800 -nc 1 -lc "cO202109111" -po 600 -lp "NWW1" -ll "4570" -sd "2021-11-11" -so "VA09" -w 40 -os 3 -sr 0 -bag browser@apiict03.etsii.upm.es -lag log@apiict03.etsii.upm.es -u launcher@apiict03.etsii.upm.es -p DynReact &
sleep 15
nohup /usr/bin/python3 ./launcher.py -oc "O202109-03" -sg "X400" -at 0.3 -wi 600 -nc 1 -lc "cO202109110" -po 600 -lp "NWW3" -ll "4510" -sd "2021-11-11" -so "VA09" -w 40 -os 8 -sr 0 -bag browser@apiict03.etsii.upm.es -lag log@apiict03.etsii.upm.es -u launcher@apiict03.etsii.upm.es -p DynReact &
sleep 15
nohup /usr/bin/python3 ./launcher.py -oc "O202109-05" -sg "X400" -at 0.7 -wi 900 -nc 1 -lc "cO202109112" -po 600 -lp "NWW3" -ll "4500" -sd "2021-11-11" -so "VA09" -w 40 -os 3 -sr 1 -bag browser@apiict03.etsii.upm.es -lag log@apiict03.etsii.upm.es -u launcher@apiict03.etsii.upm.es -p DynReact &
sleep 15

nohup /usr/bin/python3 ./launcher.py -oc "O202109-01" -sg "X400" -at 0.3 -wi 985 -nc 4 -lc "cO202109101,cO202109102,cO202109103,cO202109104" -po 2400 -lp "NWW3,NWW1,NWW1,NWW3" -ll "4500,4200,4000,5000" -sd "2021-11-11" -so "VA09" -w 40 -os 8 -bag browser@apiict03.etsii.upm.es -lag log@apiict03.etsii.upm.es -u launcher@apiict03.etsii.upm.es -p DynReact &
sleep 15

nohup /usr/bin/python3 ./launcher.py -oc "O202109-02" -sg "X400" -at 0.3 -wi 980 -nc 4 -lc "cO202109105,cO202109106,cO202109107,cO202109108" -po 2400 -lp "NWW3,NWW1,NWW1,NWW3" -ll "4600,4700,4100,4000" -sd "2021-11-11" -so "VA09" -w 40 -os 3 -bag browser@apiict03.etsii.upm.es -lag log@apiict03.etsii.upm.es -u launcher@apiict03.etsii.upm.es -p DynReact &
sleep 5
#nohup /usr/bin/python3 ./launcher.py -oc "354159" -sg "X400" -at 0.63 -wi 1014 -nc 3 -lc "694-1,694-2,694-3" -po 2000 -lp "NWW3,NWW3,NWW3" -ll "4284,4095,4219" -sd "2021-11-14" -so "VA12" -w 400  -bag browser@apiict00.etsii.upm.es  -lag log@apiict00.etsii.upm.es  -u launcher@apiict00.etsii.upm.es  -p DynReact 


/usr/bin/python3 ./va.py -an 9 -sd 0.28 -lag log@apiict03.etsii.upm.es -bag browser@apiict03.etsii.upm.es -u va09@apiict03.etsii.upm.es -p DynReact
sleep 5