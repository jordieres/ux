#!/bin/bash
#
nohup /usr/bin/python3 /home/jb/soft/dynreact/launcher.py -oc "O202109-01" -sg "X400" -at 0.3 -wi 985 -nc 4 -lc "cO202109101, cO202109102, cO202109103,cO202109104" -po 2000 -lp "NWW1,NWW1,NWW1,NWW1" -ll "4000,4100,5000,4150" -sd "2021-11-10" -so "VA08" -w 40 -bag browser@apiict00.etsii.upm.es -lag log@apiict00.etsii.upm.es -u launcher@apiict00.etsii.upm.es -p DynReact &
sleep 15
# nohup /usr/bin/python3 /home/jb/soft/dynreact/launcher.py -oc "O202109-02" -sg "X400" -at 0.3 -wi 985 -nc 1 -lc "cO202109105" -po 600 -lp "NWW1" -ll "21500" -sd "2021-11-11" -so "VA08" -w 40 -bag browser@apiict00.etsii.upm.es -lag log@apiict00.etsii.upm.es -u launcher@apiict00.etsii.upm.es -p DynReact &
sleep 15
/usr/bin/python3 /home/jb/soft/dynreact/launcher.py --search aa=list -w 40 -bag browser@apiict00.etsii.upm.es -lag log@apiict00.etsii.upm.es -u launcher@apiict00.etsii.upm.es -p DynReact
sleep 5
# nohup /usr/bin/python3 -m pdb nww.py -an 1 -lag log@apiict00.etsii.upm.es -bag browser@apiict00.etsii.upm.es -u nww1@apiict00.etsii.upm.es -p DynReact &
# sleep 5
# nohup /usr/bin/python3 /home/jb/agents_barja00/nww.py -an 1 &
# sleep 5
# nohup /usr/bin/python3  va.py -an 8 -sd 0.28 -lag log@apiict00.etsii.upm.es -bag browser@apiict00.etsii.upm.es -u va08@apiict00.etsii.upm.es -p DynReact &
# sleep 5
# /usr/bin/python3 /home/jb/soft/dynreact/coil.py -w 1200 -v 40 -st 1500 -s on -l L -b 150 -c cO202109104 -o O202109-01 -ah 900 -ll 21000 -thk 0.8 -sg X400 -an 3 -ph VA08 -bag browser@apiict00.etsii.upm.es -lag log@apiict00.etsii.upm.es -u c003@apiict00.etsii.upm.es -p DynReact
# sleep 5
# /usr/bin/python3 /home/jb/soft/dynreact/launcher.py -oc "O202109-02" -sg "X400" -at 0.4 -wi 985 -nc 1 -lc "cO202109105" -po 600 -lp "K" -ll "21500" -so "VA08" -w 40 -bag browser@apiict00.etsii.upm.es -lag log@apiict00.etsii.upm.es -u launcher@apiict00.etsii.upm.es -p DynReact
# /usr/bin/python3 /home/jb/soft/dynreact/coil.py -w 12000 -v 40 -st 15000 -s on -l K -b 150 -c cO202109105 -o O202109-02 -an 4 -ph VA08 -ah 985 -sg X400 -thk 0.35 -ll 21200 -bag browser@apiict00.etsii.upm.es -lag log@apiict00.etsii.upm.es -u c004@apiict00.etsii.upm.es -p DynReact
