#!/bin/bash
#
nm=2
ip=5010
sp=$nm+$ip
for (( i=$ip; i<$sp; i++ ))
do
   a=`ps ax | grep streamlit | grep $i | wc -l`;
   if [ "$a" -eq "0" ]; then
      streamlit run server.py --server.port=$i -- -m 138.100.82.180 138.100.82.175 -p apiict00.etsii.upm.es apiict01.etsii.upm.es apiict03.etsii.upm.es --log_mach 138.100.82.180  > /dev/null &
   fi
done
