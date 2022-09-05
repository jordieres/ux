from inspect import trace
import sys,os, subprocess, argparse
import time,datetime, ast, json
import tempfile, re, pdb
from pathlib import Path
import csv
#
import numpy as np 
import pandas as pd
import streamlit as st
#
from urllib.error import URLError
from argparse import ArgumentParser
from ast import literal_eval
#
#
# En este script en vez de tener la posibilidad de elegir cualquier máquina para ejecutar el log y
# el browser, en esta primera sección del General Status
# Se establece una única máquina, para poder simplificar el proceso y mejorar la experiencia del usuario,
# ya que el usuario se preocupa únicamente desde dónde.
# Se ha lanzado las órdenes, los agentes bobina y los agentes planta.
# En un principio se ha elegido pasar el argumento por pantalla con la ayuda de la función argparse.
# Pero no se descarta la opción de que el usuario también pueda elegir la máuina para ejecutar el log
# también al comienzo, cuando elige la plataforma donde se va a desarrollar todo el programa.
#  Aunque se considera que esta forma no queda igual de bien visualmente para la experiencia del usuario.
#
st.set_page_config(
    page_title='UX Industry Process Optimizer',
    page_icon="🖖",
    layout='wide',
    initial_sidebar_state='auto'
)
#
#st.markdown(html_string, unsafe_allow_html=True)
st.markdown("<style>.element-container{opacity:1 !important}</style>", unsafe_allow_html=True)

DEFAULT = '-- Pick a value --'
DEFAULT_pltfrm = '-- Select Platform --'
DEFAULT_mchn   = '-- Select Plant Machine --'
DEFAULT_ordrs  = '-- Select Service Machine --'
DEFAULT_plnts  = '--Select a Plant Agent--'
DEFAULT_outcm  = 'Server'
DEFAULT_outcm_ordr  = 'Order'
DEFAULT_outcm_plnt  = 'Plant'
DEFAULT_outcm_coil  = 'Coil'
#
st.markdown("""
    <style>
        div[role="listbox"] ul {
            background-color: #ADD8E6;
        }
        div[data-baseweb="select"] > div {
            background-color: #ffffff;
        }
    </style>
""", unsafe_allow_html=True,
)
#
st.markdown(""" 
    <style>
        div.stButton > button:first-child {
            background-color: #ADD8E6;color:#ffffff
        }
        div.stButton > button:hover {
            background-color: #0033CC;color:#ADD8E6;
        }
    </style>
""", unsafe_allow_html=True)
#
def selectbox_with_default(obj, values, default, text = '', sidebar = False):
    func = obj.sidebar.selectbox if sidebar else obj.selectbox
    return func(text, np.insert(np.array(values,object),0,default))
#
def get_directory(log_mach):
    oshl = 'rsh '+str(log_mach)+' mktemp -d -p . '
    out  = subprocess.Popen(oshl, stdout=subprocess.PIPE, stdin=None, stderr=None, \
                        close_fds=True, shell=True, universal_newlines = True)
    my_dict, err_1 = out.communicate()
    return(my_dict.strip())
#
def turn_on_systm(log_mach):
    # crear my_dir
    # primero tengo que copiar los files de los agents y luego puedo ejecutarlos
    # Para que se ejecute en otra máquina hay que poner delante la máquina remota que lo va a ejecutar
    my_dict= get_directory(log_mach)
    oshl_1 = 'cd agents; scp *.py @'+str(log_mach)+':'+my_dict + '/'
    res = subprocess.Popen(oshl_1, stdout=subprocess.PIPE, stdin=None, \
                        stderr=subprocess.PIPE, close_fds=True, shell=True)
    return(my_dict)
#
def initialize_agents(machine, platform, password, my_dict):
    if platform != DEFAULT_pltfrm:
        log     = 'log@' + str(platform)
        browser = 'browser@' + str(platform)
        launcher= 'launcher@' + str(platform)
        fd,path = tempfile.mkstemp(prefix='tmp_',dir='/tmp/')
        fp = os.fdopen(fd,'w')
        fp.write("#! /bin/bash\n\ncd " + str(my_dict)+'\n')
        fp.write('/usr/bin/nohup /usr/bin/python3 ./log.py ' +\
                '-bag '+str(browser)+' -u '+str(log)+' -p '+password+' -w 900 &\n')
        fp.write('sleep 2\n')
        fp.write('/usr/bin/nohup /usr/bin/python3 ./browser.py ' +\
                ' -u '+str(browser)+' -p '+password+' -lag '+str(log)+ \
                ' -lhg '+str(launcher)+' -w 900 &\n')
        fp.close()
        subprocess.call(['chmod','0755',path])
        oshl = " scp -p " + path + " @" + str(machine) +":" + my_dict + "/agorden.sh"
        err0 = subprocess.Popen(oshl, stdout=subprocess.PIPE, stdin=None, \
                            stderr=subprocess.PIPE, close_fds=True, shell=True)
        oshl1= 'rsh '+str(machine)+ ' "sh ' + str(my_dict) + '/agorden.sh"'
        time.sleep(2)
        err1 = subprocess.Popen(oshl1, stdout=subprocess.PIPE, stdin=None, \
                            stderr=subprocess.PIPE, close_fds=True, shell=True)
        os.remove(path)
    return(None)
#
def check_agents(machine, platform, password,my_dict):
    if platform != DEFAULT_pltfrm:
        cmd  = " ps aux |grep python3 |grep log.py | grep " + platform + " | grep -v grep | wc -l"
        oshl = 'rsh '+str(machine) + cmd
        out_1= subprocess.Popen(oshl, stdout=subprocess.PIPE, stdin=None, stderr=None, \
                            close_fds=True, shell=True)
        logst, err_1 = out_1.communicate()
        #
        cmd  = " ps aux |grep python3 |grep browser.py | grep " + platform + " | grep -v grep | wc -l"
        oshl = 'rsh '+str(machine) + cmd
        out_1= subprocess.Popen(oshl, stdout=subprocess.PIPE, stdin=None, stderr=None, \
                            close_fds=True, shell=True)
        brwst, err_2 = out_1.communicate()
    else:
        logst= '0'
        brwst= '0'
    #
    return (int(logst),int(brwst))
#
def kill_agents(machine, my_dict,kill_log, kill_brw):
    fd,path = tempfile.mkstemp(prefix='tmp_',dir='/tmp/')
    fp = os.fdopen(fd,'w')
    if kill_brw > 0:
        fp.write("/usr/bin/kill -9 `ps ax |grep browser.py |grep -v grep ")
        fp.write("| awk '{print $1}'`\n")
    if kill_log > 0:
        fp.write("/usr/bin/kill -9 `ps ax |grep log.py |grep -v grep ")
        fp.write("| awk '{print $1}'`\n")
    fp.close()
    oshl = " scp " + path + " @" + str(machine) +":" + my_dict + "/klorden.sh"
    err = subprocess.Popen(oshl, stdout=subprocess.DEVNULL, stdin=None, \
                        stderr=subprocess.DEVNULL, close_fds=True, shell=True)
    oshl1= 'rsh '+str(machine)+ ' "sh ' + str(my_dict) + '/klorden.sh"'
    time.sleep(2)
    err = subprocess.Popen(oshl1, stdout=subprocess.PIPE, stdin=None, \
                        stderr=subprocess.PIPE, close_fds=True, shell=True)
    os.remove(path)
    return(None)
#
def procesa_reg(cad):
    pid = cad.split(' ')[0]
    cmds= cad.split('coil.py')[1].strip().split(' ')
    keys= cmds[0:len(cmds):2]
    vals= cmds[1:len(cmds):2]
    idx = {'idcoil':'-an','plans':'-ph','width':'-ah','mat':'-sg','thickness':'-thk',\
           'length':'-ll','from':'-l','order': '-o','coilname':'-c','user':'-u',\
           'password':'-p','duedate':'-sd','factorf':'-F','budget':'-b'}
    dct = {'pid':pid}
    for i in idx.keys():
        dct[i] = vals[keys.index(idx[i])]
    return(dct)
#
def procesa_plt(cad):
    lps = cad.split(' ')
    pid = lps[0]
    rr  = re.compile(".*\.py")
    gg  = list(filter(rr.match,lps))
    plt = gg[0].split('/')[-1].split('.')[0].upper()
    cmds= cad.split('.py')[1].strip().split(' ')
    keys= cmds[0:len(cmds):2]
    vals= cmds[1:len(cmds):2]
    nam = vals[keys.index('-u')].split('@')[0]
    idx = {'idplt':'-an','sd':'-sd','user':'-u','password':'-p'}
    dct = {'pid':pid,'plant':plt,'pltname':nam}
    for i in idx.keys():
        dct[i] = vals[keys.index(idx[i])]
    return(dct)
#
def list_coils_orders_active(pltf, log, browser, launcher, my_dict, password):
    n_orders = 0
    n_coils  = 0
    lst_coils= pd.DataFrame(columns=['launch_machine','pid','idcoil', 'plans', 'width', 'mat', \
                                'thickness', 'length', 'from', 'order', 'coilname', \
                                'user', 'password', 'duedate', 'factorf', 'budget'])
    #
    for j in st.session_state['mchnvec_ordr'][pltf]['dirs'].keys(): #recorre el nombre de las maquinas
        rdir = st.session_state['mchnvec_ordr'][pltf]['dirs'][j]
        if len(rdir) > 0:
            olcs = "rsh " + str(j) + "  ps -ax | grep coil.py | grep '"
            olcs = olcs + rdir + "' | grep -v grep "
            out  = subprocess.Popen(olcs, stdout=subprocess.PIPE, stdin=None, \
                            stderr=subprocess.PIPE,close_fds=True, shell=True, \
                            universal_newlines = True)
            outlst, err = out.communicate()
            lst_objs    = outlst.split('\n')
            lsts        = []
            for i in lst_objs:
                if len(i) > 0:
                    lsts.append(procesa_reg(i))
            lst_coils = pd.concat([lst_coils,pd.DataFrame(lsts)],axis=0)
            n_coils   = len(lst_coils['coilname'].unique().tolist())
            n_orders  = len(lst_coils['order'].unique().tolist())
    return n_coils , n_orders , lst_coils
#
def list_plants_active(pltf, log, browser, launcher, my_dict,password):
    lst_plnts= pd.DataFrame(columns=['pid','plant','pltname','idplt','sd',\
                                     'user','password'])
    n_plants = 0
    for j in st.session_state['mchnvec_plnt'][pltf]['dirs'].keys():
        rdir = st.session_state['mchnvec_plnt'][pltf]['dirs'][j]
        if len(rdir) > 0:
            olcs = "rsh "+str(j)+" ps -ax | grep python3 | grep "+rdir
            olcs = olcs + " | grep -v coil.py | grep -v browser.py | grep -v grep "
            olcs = olcs + " | grep -v log.py | grep -v launcher.py "
            out  = subprocess.Popen(olcs, stdout=subprocess.PIPE, stdin=None, \
                                stderr=subprocess.PIPE,close_fds=True, shell=True, \
                                universal_newlines = True)
            outlst, err = out.communicate()
            lst_objs    = outlst.split('\n')
            lsts        = []
            for i in lst_objs:
                if len(i) > 0:
                    lsts.append(procesa_plt(i))
            lst_plnts = pd.concat([lst_plnts,pd.DataFrame(lsts)],axis=0)
            n_plants  = len(lst_plnts['pltname'].unique().tolist())
    return n_plants, lst_plnts
#
def display_table(platform, log_mach, log, browser, launcher, directory, password):
    if platform == DEFAULT_pltfrm:
        dataframe = pd.DataFrame()
        list_plants = list_coils = []
    else:
        n_coils, n_orders, list_coils = list_coils_orders_active(platform, log, browser, \
                                            launcher, directory, password)
        n_plants, list_plants = list_plants_active(platform, log, browser, \
                                            launcher,directory, password)
        log_st, brw_st = check_agents(log_mach, platform, password, directory)
        n_agents = n_coils + n_plants + log_st + brw_st
        #
        dataframe = pd.DataFrame({
            'Selected platform': [platform],
            'Status': ['Alive'],
            'Nº agents': [n_agents],
            'Nº plants': [n_plants],
            'Nº Orders': [n_orders],
            'Nº Coils': [n_coils]
        })
    return({'df':dataframe,'lpts':list_plants,'lcls':list_coils})
#
def prepare_file(uploaded_file):
    # Extract order parameters
    onm,mat,thick,wid,bud,fcts,nc = uploaded_file.loc[0]
    wid  = int(wid)
    nc   = int(nc)
    bud  = int(bud)
    lcls = uploaded_file.iloc[1:(nc+1),[0,1,2]]
    lcls.columns = ["CoilName","PltSource","CoilLength"]
    res = {'oname':onm,'mat':mat,'thick':thick,'width':wid, \
           'bdgt': bud, 'prule':fcts,'ncls':nc,'cdf':lcls}
    return(res)
#
def launch_orders(detorder, machine, my_dict, platform, password):
    log = 'log@' + str(platform)
    browser = 'browser@' + str(platform)
    launcher = 'launcher@' + str(platform)
    #nohup /usr/bin/python3 /home/jb/agents_jb03/launcher.py -oc "O202109-01" -sg "X400" -at 0.3 -wi 985 -nc 4 -lc "cO202109101, cO202109102, cO202109103,cO202109104" -po 2000 -lp "NWW1,NWW1,NWW1,NWW1" -ll "20000,21000,19500,21500" -sd "2021-11-10" -so "VA0[8-9]" -w 40 
    #-bag browser@apiict00.etsii.upm.es -lag log@apiict00.etsii.upm.es -u launcher@apiict00.etsii.upm.es -p DynReact &
    #
    lst_cns = ','.join(detorder['cdf'].loc[:,'CoilName'].tolist())
    lst_pss = ','.join(detorder['cdf'].loc[:,'PltSource'].tolist())
    lst_lgth= ','.join([str(int(k)) for k in detorder['cdf'].loc[:,'CoilLength'].tolist()])
    fd,path = tempfile.mkstemp(prefix='tmp_',dir='/tmp/')
    fp = os.fdopen(fd,'w')   
    fp.write("/usr/bin/nohup /usr/bin/python3 " + str(my_dict)+ "/launcher.py ")
    fp.write("-oc '"+str(detorder['oname'])+"' -sg '"+str(detorder['mat']))
    fp.write("' -at "+str(detorder['thick'])+ " -wi "+str(int(detorder['width'])))
    fp.write(" -nc "+str(detorder['ncls'])+" -lc '" + lst_cns + "' -po ")
    fp.write(str(int(detorder['bdgt'])) + " -lp \'" + lst_pss + "\' -ll \'")
    fp.write(lst_lgth + "' -so '" + detorder['prule'])
    fp.write("' -bag " + str(browser) + " -lag " + str(log) + " -u ")
    fp.write(str(launcher)+" -p "+password+" -w 40 &\n")
    fp.close()
    subprocess.call(['chmod','0755',path])
    oshl = " scp " + path + " @" + str(machine) +":" + my_dict + "/lchorden.sh"
    err0 = subprocess.Popen(oshl, stdout=subprocess.PIPE, stdin=None, \
                        stderr=subprocess.PIPE, close_fds=True, shell=True)
    oshl1= 'rsh '+str(machine)+ ' "sh ' + str(my_dict) + '/lchorden.sh"'
    time.sleep(2)
    err1 = subprocess.Popen(oshl1, stdout=subprocess.PIPE, stdin=None, \
                        stderr=subprocess.PIPE, close_fds=True, shell=True)
    os.remove(path)
    time.sleep(18)
    return(None)
#
def launch_plant(plant, machine, my_dict, platform, log, browser, password):
    plant = plant.lower()
    if plant not in st.session_state['mchnvec_plnt'][platform]['plnts'][machine]:
        if platform != DEFAULT_pltfrm:
            va = str(plant)+'@' + str(platform)
            #
            fd,path = tempfile.mkstemp(prefix='tmp_',dir='/tmp/')
            fp = os.fdopen(fd,'w')
            fp.write("#!/bin/bash\n\ncd " + str(my_dict)+ "\n")
            fp.write("/usr/bin/nohup /usr/bin/python3 $HOME/"+ str(my_dict)+"/va.py ")
            fp.write("-an '"+str(int(plant[-2:]))+"' -sd '"+str(0.25))
            fp.write("' -bag " + str(browser) + " -lag " + str(log) + " -u ")
            fp.write(str(va)+" -p "+password+" &\n")
            fp.close()
            subprocess.call(['chmod','0755',path])
            oshl = " scp -p "+path+" @"+str(machine)+":\$HOME/"+my_dict+"/lchplanta.sh"
            err0 = subprocess.Popen(oshl, stdout=subprocess.PIPE, stdin=None, \
                                stderr=subprocess.PIPE, close_fds=True, shell=True)
            oshl1= 'rsh '+str(machine)+ ' "sh ' + str(my_dict) + '/lchplanta.sh"'
            time.sleep(1)
            err1 = subprocess.Popen(oshl1, stdout=subprocess.PIPE, stdin=None, \
                                stderr=subprocess.PIPE, close_fds=True, shell=True)
            os.remove(path)
            if plant not in st.session_state['mchnvec_plnt'][platform]['plnts'][machine]:
                st.session_state['mchnvec_plnt'][platform]['plnts'][machine].append(plant)
    return(None)
#
def read_log_for_coil (ordr_selec,ordr_machine,coil_sel, directory_log, platform, password):
    home = str(Path.home())
    #path = home+str(directory_log[1:])+"/log.log"
    path = home+"/logtesteo.log"
    search_str_coil = 'ENDEDUP'
    search_str = '"location_2":"END"'
    #coil_selected = coil_sel+'@'+platform
    coil_selected = coil_sel+'@apiict00.etsii.upm.es'
    l_plnt= []
    l_coil = []
    n_coils_auction = []
    time_auc = []
    time_coil = []
    lst_offer = []
    lst_bids = []
    outcome = []
    df_s1 = pd.DataFrame()
    df_c = pd.DataFrame()
    pdb.set_trace()
    with open(path) as f:
        for line in f.readlines()[:]:
            if search_str in line:  # find search_str
                time = line.split(';')[0]
                time_auc.append(time)
                n = line.find("{")
                a = line[n:]
                l_plnt.append(a)
            if search_str_coil in line: 
                time = line.split(';')[0]
                time_coil.append(time)
                n_c = line.find("msg")
                a_c = line[n_c:]
                l_coil.append(a_c)
    df_0 = pd.DataFrame(l_plnt, columns=['register'])
    df_1 = pd.DataFrame(l_coil, columns=['register'])
    if not(df_1.empty):
        for ind in df_1.index:
            if ind == 0:
                #2022-06-17 11:18:44,442;INFO;coil;./log.py;[{"purpose":"inform log","from":"c006@apiict00.etsii.upm.es","id":"c006@apiict00.etsii.upm.es","to":"log@apiict00.etsii.upm.es","msg":"ENDEDUP: c006@apiict00.etsii.upm.es, code:CO202110-073-07 , order: O202110-073, by: 2022-06-17 11:18:44, offer: 673.2"}]
                #ver si esto se puede reescribir y cambiar el espacio de code
                #hay que filtrar por order
                linea = df_1.loc[ind, 'register'].split('"')[2].split(' ')
                keys= linea[0:len(linea):2]
                offer = keys[-1]
                vals= linea[1:len(linea):2]
                idx = {'wincoil':'ENDEDUP:','code':'code:','Order':'order:'}
                dct = {'Order':ordr_selec, 'order machine':ordr_machine, 'offer':offer}
                for i in idx.keys():
                    dct[i] = vals[keys.index(idx[i])]
                df_s1 = pd.DataFrame.from_dict([dct])
                lst_offer.append(offer)
            else:
                linea_1 = df_1.loc[ind, 'register'].split('"')[2].split(' ')
                keys_1= linea_1[0:len(linea_1):2]
                offer_1 = keys_1[-1]
                vals_1= linea_1[1:len(linea_1):2]
                idx_1 = {'wincoil':'ENDEDUP:','code':'code:','Order':'order:'}
                dct_1 = {'Order':ordr_selec, 'order machine':ordr_machine,'offer':offer_1}
                for i in idx_1.keys():
                    dct_1[i] = vals_1[keys_1.index(idx_1[i])]
                c = pd.DataFrame.from_dict([dct_1])
                df_s1 = df_s1.append(c)
                lst_offer.append(offer_1)
    if not(df_0.empty):
        for ind in df_0.index:
            if ind == 0:
                element1 = df_0.loc[ind, 'register'].split('{')[1].split(',"gantt":')[0]
                element2 = df_0.loc[ind, 'register'].split('{')[-1].split('}')[2].split(']')[0]
                element = '{'+ element1+element2+'}'
                z = json.loads(element) #dictionary
                active_coils_0 = z.pop('active_coils')
                n_coils_auction.append(len(set(active_coils_0)))
                auction_coils = z.pop('auction_coils')
                if z['coil_auction_winner'] == coil_selected:
                    outcome.append('WON')
                else:
                    outcome.append('LOST')
                lst_bids.append(z['bid'])
                df = pd.DataFrame.from_dict([z])
            else:
                element_1 = df_0.loc[ind, 'register'].split('{')[1].split(',"gantt":')[0]
                element_2 = df_0.loc[ind, 'register'].split('{')[-1].split('}')[2].split(']')[0]
                element = '{'+ element_1+element_2+'}'
                y = json.loads(element)
                active_coils = y.pop('active_coils')
                n_coils_auction.append(len(set(active_coils)))
                auction_coils = y.pop('auction_coils')
                if len(set(outcome)) == 1 : #check if the coil has already won
                    lst_bids.append(y['bid'])
                    if y['coil_auction_winner'] == coil_selected:
                        outcome.append('WON')
                    else:
                        outcome.append('LOST')
                b = pd.DataFrame.from_dict([y])
                df = df.append(b)
    #df for order
    df_s1['offers'] = lst_offer
    df_s1['time_ordr'] = time_coil
    df_s1['n_coils_auction'] = n_coils_auction
    df_s1 = df_s1.reset_index(drop=True)
    #df for the coil
    d ={'time_coil' : time_coil[:len(outcome)],
            'offers' : lst_bids,
            'outcome' : outcome
        }
    df_c = pd.DataFrame.from_dict(d)
    return(df_s1, df_c)
#
def read_log_for_plnt(plant_selec,plant_machine, directory_log, platform, password, coil_sel = 'c009'):
    home = str(Path.home())
    #path = home+str(directory_log[1:])+"/log.log"
    path = home+"/logtesteo.log"
    #search_str = '{"id":"'+plant_selec+'@'+platform+'","agent_type":"VA","location_1"'
    search_str = '{"id":"va09@apiict00.etsii.upm.es","agent_type":"VA","location_1"'
    search_str_coil = 'ENDEDUP'
    #coil_selected = coil_sel+'@'+platform
    coil_selected = coil_sel+'@apiict00.etsii.upm.es'
    l_plnt= []
    l_coil = []
    n_coils_auction = []
    time_auc = []
    time_coil = []
    lst_offer = []
    lst_bids = []
    outcome = []
    df = pd.DataFrame()
    df_s1 = pd.DataFrame()
    df_c = pd.DataFrame()
    with open(path) as f:
        for line in f.readlines()[:]:
            if search_str in line:  # find search_str
                time = line.split(';')[0]
                time_auc.append(time)
                n = line.find("{")
                a = line[n:]
                l_plnt.append(a)
            if search_str_coil in line: 
                time = line.split(';')[0]
                time_coil.append(time)
                n_c = line.find("msg")
                a_c = line[n_c:]
                l_coil.append(a_c)
    df_0 = pd.DataFrame(l_plnt, columns=['register'])
    df_1 = pd.DataFrame(l_coil, columns=['register'])
    if not(df_1.empty):
        for ind in df_1.index:
            if ind == 0:
                #2022-06-17 11:18:44,442;INFO;coil;./log.py;[{"purpose":"inform log","from":"c006@apiict00.etsii.upm.es","id":"c006@apiict00.etsii.upm.es","to":"log@apiict00.etsii.upm.es","msg":"ENDEDUP: c006@apiict00.etsii.upm.es, code:CO202110-073-07 , order: O202110-073, by: 2022-06-17 11:18:44, offer: 673.2"}]
                #ver si esto se puede reescribir y cambiar el espacio de code
                linea = df_1.loc[ind, 'register'].split('"')[2].split(' ')
                keys= linea[0:len(linea):2]
                offer = keys[-1]
                vals= linea[1:len(linea):2]
                idx = {'wincoil':'ENDEDUP:','code':'code:','order':'order:'}
                dct = {'plant':plant_selec, 'plant machine':plant_machine, 'offer':offer}
                for i in idx.keys():
                    dct[i] = vals[keys.index(idx[i])]
                df_s1 = pd.DataFrame.from_dict([dct])
                lst_offer.append(offer)
            else:
                linea_1 = df_1.loc[ind, 'register'].split('"')[2].split(' ')
                keys_1= linea_1[0:len(linea_1):2]
                offer_1 = keys_1[-1]
                vals_1= linea_1[1:len(linea_1):2]
                idx_1 = {'wincoil':'ENDEDUP:','code':'code:','order':'order:'}
                dct_1 = {'plant':plant_selec, 'plant machine':plant_machine,'offer':offer_1}
                for i in idx_1.keys():
                    dct_1[i] = vals_1[keys_1.index(idx_1[i])]
                c = pd.DataFrame.from_dict([dct_1])
                df_s1 = df_s1.append(c)
                lst_offer.append(offer_1)
    if not(df_0.empty):            
        for ind in df_0.index:
            if ind == 0:
                element1 = df_0.loc[ind, 'register'].split('{')[1].split(',"gantt":')[0]
                element2 = df_0.loc[ind, 'register'].split('{')[-1].split('}')[2].split(']')[0]
                element = '{'+ element1+element2+'}'
                z = json.loads(element) #dictionary
                active_coils_0 = z.pop('active_coils')
                n_coils_auction.append(len(set(active_coils_0)))
                auction_coils = z.pop('auction_coils')
                if z['coil_auction_winner'] == coil_selected:
                    outcome.append('WON')
                else:
                    outcome.append('LOST')
                lst_bids.append(z['bid'])
                df = pd.DataFrame.from_dict([z])
            else:
                element_1 = df_0.loc[ind, 'register'].split('{')[1].split(',"gantt":')[0]
                element_2 = df_0.loc[ind, 'register'].split('{')[-1].split('}')[2].split(']')[0]
                element = '{'+ element_1+element_2+'}'
                y = json.loads(element)
                active_coils = y.pop('active_coils')
                n_coils_auction.append(len(set(active_coils)))
                auction_coils = y.pop('auction_coils')
                if len(set(outcome)) == 1 : #check if the coil has already won
                    lst_bids.append(y['bid'])
                    if y['coil_auction_winner'] == coil_selected:
                        outcome.append('WON')
                    else:
                        outcome.append('LOST')
                b = pd.DataFrame.from_dict([y])
                df = df.append(b)
        #df for the plant
        df['n_coils_auction'] = n_coils_auction
        df['time_auc'] = time_auc
        df = df.reset_index(drop=True)
        #df for server
        df_s1['offers'] = lst_offer
        df_s1['time_server'] = time_coil
        df_s1['n_coils_auction'] = n_coils_auction
        df_s1 = df_s1.reset_index(drop=True)
    return(df, df_s1)

def execute_coil(ordr_selec,ordr_machine,outcm_coil, log_mach,directory_log, platform, password):
    home = str(Path.home())
    df_ordr, df_coil = read_log_for_coil (ordr_selec,ordr_machine,outcm_coil, directory_log, platform, password)
    keys_ordr = ['time_ordr','wincoil','code','Order','offers','n_coils_auction']
    lst_ordrhead = ['Time Auction Finished','Winner Coil','Coil Order Code','Order','Offer', 'Nº of Coils in Auction']
    lst_coilhead = ['Time Auction','Offer','Outcome']
    df_ordr = df_ordr[keys_ordr]
    df_ordr.columns = lst_ordrhead
    df_ordr = df_ordr.sort_values(by = ['Time Auction Finished'], ascending = False)
    #
    df_coil.columns = lst_coilhead
    df_coil.columns = df_coil.sort_values(by = ['Time Auction'], ascending = False)
    return (df_ordr, df_coil)

def execute_plant(plant_selec,plant_machine, log_mach,directory_log, platform, password):     
    df, df_1 = read_log_for_plnt(plant_selec,plant_machine, directory_log, platform, password)
    keys_plnt = ['time_auc','auction_number','coil_auction_winner','n_coils_auction','bid','Profit']
    lst_plnthead = ['Time Auction Finished','Nº of Auction','Winner Coil','Nº of Coils in Auction','Winner Value', 'Profit']
    keys_server = ['time_server','wincoil','code','order','offers','n_coils_auction']
    lst_serverhead = ['Time Auction Finished','Winner Coil','Coil Order Code','Order','Offer', 'Nº of Coils in Auction']
    #
    df_server = df_1[keys_server]
    df_server.columns = lst_serverhead
    df_server = df_server.sort_values(by = ['Time Auction Finished'], ascending = False)
    #
    df_plnt = df[keys_plnt]
    df_plnt.columns = lst_plnthead
    df_plnt = df_plnt.sort_values(by = ['Time Auction Finished'], ascending = False)
    return (df_plnt,df_server)
#
def tabs(obj,default_tabs = [], default_active_tab=0):
    #https://discuss.streamlit.io/t/multiple-tabs-in-streamlit/1100/21
    if not default_tabs:
        return None
    active_tab = obj.radio("", default_tabs, index=default_active_tab, key='tabs')
    child = default_tabs.index(active_tab)+1
    obj.markdown("""  
        <style type="text/css">
            div[role=radiogroup] > label > div:first-of-type, .stRadio > label {
                display: none;               
            }
            div[role=radiogroup] {
                flex-direction: unset
            }
            div[role=radiogroup] label {             
                border: 1px solid #999;
                background: #EEE;
                padding: 4px 12px;
                border-radius: 4px 4px 0 0;
                position: relative;
                top: 1px;
            }
            div[role=radiogroup] label:nth-child(""" + str(child) + """) {    
                background: #FFF !important;
                border-bottom: 1px solid transparent;
            }            
        </style>
    """,unsafe_allow_html=True)        
    return(active_tab)
#
def init_vars(lft,cnt,platform):
    if 'directory_log' not in st.session_state:
        st.session_state['directory_log']= None
    if 'pltfrm' not in st.session_state:
        st.session_state['pltfrm']       = None
        #if platform == DEFAULT_pltfrm:
        #    lft.header('Welcome!')
        #    lft.write('Here you will manage your Multi-agent System.')
        #    lft.write('You will be able of keeping track of your agents and bids, their statuses and even uploading order forms and launching them!')
        #    st.warning('Please, to start the session you need to pick a value')
        #    cnt.image('logo2.png', use_column_width = True)
    if 'pltvec' not in st.session_state:
        st.session_state['pltvec']       = {}
    if 'mchn_ordr' not in st.session_state:
        st.session_state['mchn_ordr']    = DEFAULT_ordrs
    if 'mchnvec_ordr' not in st.session_state:
        st.session_state['mchnvec_ordr'] = {}
    if 'mchn_plnt' not in st.session_state:
        st.session_state['mchn_plnt']    = DEFAULT_mchn
    if 'mchnvec_plnt' not in st.session_state:
        st.session_state['mchnvec_plnt'] = {}
    if 'areaordrs' not in st.session_state:
        st.session_state['areaordrs']    = None
    #
    return(None)
#
def setup(platform,log_mach,log, browser, launcher,password):
    df_st = pd.DataFrame()
    directory_log = ''
    if platform in st.session_state['mchnvec_ordr'].keys() :
        directory_log = st.session_state['mchnvec_ordr'][platform]['pltd']
    elif platform != DEFAULT_pltfrm:
        directory_log = turn_on_systm(log_mach)
        print(directory_log, 'directory del log')
        
        #  Machine on the Order section
        st.session_state['mchnvec_ordr'][platform] = {}
        st.session_state['mchnvec_ordr'][platform]['srvn'] = log_mach # machine for log/browser
        st.session_state['mchnvec_ordr'][platform]['pltd'] = directory_log # directory for log/browser in log_mach       
        st.session_state['mchnvec_ordr'][platform]['ords'] = {} # list of files per machine
        st.session_state['mchnvec_ordr'][platform]['lnos'] = {} # list of order codes per machine
        st.session_state['mchnvec_ordr'][platform]['dirs'] = {} # directory per machine
        st.session_state['mchnvec_ordr'][platform]['clts'] = [] # list of coils machine
        #  Machine on the Plant section
        st.session_state['mchnvec_plnt'][platform] = {}
        st.session_state['mchnvec_plnt'][platform]['srvn'] = log_mach # machine for log/browser
        st.session_state['mchnvec_plnt'][platform]['pltd'] = directory_log # directory for log/browser in log_mach
        st.session_state['mchnvec_plnt'][platform]['plnts']= {}
        st.session_state['mchnvec_plnt'][platform]['dirs'] = {} # directory per machine
        st.session_state['mchnvec_plnt'][platform]['clts'] = [] # list of plants machine
    if len(directory_log) > 0:
        st.session_state['directory_log'] = directory_log
    if platform != DEFAULT_pltfrm:
        st.session_state['pltfrm'] = platform
        res   = display_table(platform, log_mach, log, browser, launcher, \
                            directory_log, password)
        df_list_plnts = res['lpts']
        df_list_coils = res['lcls']
        df_st = res['df']
        if df_st.shape[0] > 0:
            df_st.set_index('Selected platform',inplace=True) 
    return(directory_log, df_st)
#
def restart_vars(platform,log_mach,log, browser, launcher,password):
    st.session_state['directory_log']= None
    st.session_state['pltfrm']       = None
    st.session_state['pltvec']       = {}
    st.session_state['mchn_ordr']    = DEFAULT_ordrs
    st.session_state['mchnvec_ordr'] = {}
    st.session_state['mchn_plnt']    = DEFAULT_mchn
    st.session_state['mchnvec_plnt'] = {}
    st.session_state['areaordrs']    = None
    #
    x,y = setup(platform,log_mach,log, browser, launcher,password)
    return(None)
#
def setup_order(platform,machine):
    if machine in st.session_state['mchnvec_ordr'][platform]['ords'].keys() :
        lst_orders = st.session_state['mchnvec_ordr'][platform]['ords'][machine]
    else:
        lst_orders = []
        st.session_state['mchnvec_ordr'][platform]['ords'][machine] = lst_orders
        st.session_state['mchnvec_ordr'][platform]['lnos'][machine] = []                
        st.session_state['mchnvec_ordr'][platform]['dirs'][machine] = ''
        st.session_state['mchnvec_ordr'][platform]['clts'].append(machine)
    st.session_state['mchn_ordr'] = machine
    return(lst_orders)
#
def setup_plant(platform,machine):
    if machine in st.session_state['mchnvec_plnt'][platform]['plnts'].keys() :
        lst_plnts = st.session_state['mchnvec_plnt'][platform]['plnts'][machine]
    else:
        lst_plnts = []
        st.session_state['mchnvec_plnt'][platform]['plnts'][machine] = lst_plnts
        st.session_state['mchnvec_plnt'][platform]['dirs'][machine] = ''
        st.session_state['mchnvec_plnt'][platform]['clts'].append(machine)
    st.session_state['mchn_plnt'] = machine
    return(lst_plnts)
#
def update_order(platform,machine,log_mach,ordf,uploaded_file):
    if 'detord' in st.session_state:
        detord = st.session_state['detord']
    else:
        detord = {}
    if platform in st.session_state['mchnvec_ordr'].keys():
        directory_log = st.session_state['mchnvec_ordr'][platform]['pltd']
    if len(st.session_state['mchnvec_ordr'][platform]['dirs'][machine]) == 0:
        if machine != log_mach:
            dir_orders= turn_on_systm(machine)
            st.session_state['mchnvec_ordr'][platform]['dirs'][machine]=dir_orders
        else:
            dir_orders= directory_log
            st.session_state['mchnvec_ordr'][platform]['dirs'][machine]=dir_orders
    else:
        dir_orders= st.session_state['mchnvec_ordr'][platform]['dirs'][machine]
    # # Processing the orders file if not yet done
    if ordf != DEFAULT and 'detord' not in st.session_state:
        if ordf not in st.session_state['mchnvec_ordr'][platform]['ords'][machine]:
            csv_file = pd.read_csv(uploaded_file,header=None, comment='#')
            csv_file = csv_file.iloc[:,0:7]
            detord   = prepare_file(csv_file)
            st.session_state['detord'] = detord
        else:
            st.session_state.pop('detord')
    return(detord)
#
def update_plant(platform,machine,log_mach,plnt):
    if platform in st.session_state['mchnvec_plnt']:
        directory_log = st.session_state['mchnvec_plnt'][platform]['pltd']
    if len(st.session_state['mchnvec_plnt'][platform]['dirs'][machine]) == 0:
        if machine   != log_mach:
            dir_plnts = turn_on_systm(machine)
            st.session_state['mchnvec_plnt'][platform]['dirs'][machine]=dir_plnts
        else:
            dir_plnts = directory_log
            st.session_state['mchnvec_plnt'][platform]['dirs'][machine]=dir_plnts
    else:
        dir_plnts = st.session_state['mchnvec_plnt'][platform]['dirs'][machine]
    lst_plnts = st.session_state['mchnvec_plnt'][platform]['plnts'][machine]    
    return(lst_plnts)
#
def order_process(platform,machine,detord,ordf,password):
    #lanzar órdenes
    dir_orders = st.session_state['mchnvec_ordr'][platform]['dirs'][machine]
    launch_orders(detord,machine,dir_orders,platform,password)                    
    st.session_state['mchnvec_ordr'][platform]['ords'][machine].append(ordf)
    st.session_state['mchnvec_ordr'][platform]['lnos'][machine].append(detord)
    return(None)
#
#
#
#
def main():
    #
    # ==================================================================================================
    # Main program
    #
    parser = argparse.ArgumentParser()
    # streamlit run nuevo.py -- --machines 138.100.82.175 138.100.82.241 --platforms apiict00.etsii.upm.es --platforms apiict01.etsii.upm.es
    parser.add_argument('-m','--machines',nargs='+', type=str, \
                        help='Available machines for plants and coils.')
    parser.add_argument('-p','--platforms',nargs='+', type=str, \
                        help='Available negotiation platforms.')
    parser.add_argument('-l','--log_mach', type=str, \
                        help="Machine where the log.log file is going to be stored")
    #
    #Name convention columns: location on the page_section of the program
    #
    args            = argparse.Namespace()
    args            = parser.parse_args()
    machines_parser = args.machines
    platforms_parser= args.platforms
    log_mach        = args.log_mach
    password        = 'DynReact'
    df        = pd.DataFrame({
        'apiict': platforms_parser})
    df2       = pd.DataFrame({
        'machines': machines_parser})
    yes_no    = pd.DataFrame({
        'check': ['Yes', 'No']})
    df3       = df2
    main_tabs = ['ORDERS','PLANTS','OUTCOME']
    optplnts  = (DEFAULT_plnts,'VA08','VA09','VA10','VA11','VA12','VA13')
    #
    st.empty()
    title_container = st.container()
    #
    left_gnrlsect, center_gnrlsect, right_gnrlsect = title_container.columns((2,4,1))
    left_gnrlsect.image('logo.png', width=128)
    #
    platform = selectbox_with_default(center_gnrlsect, df['apiict'], DEFAULT_pltfrm)
    log      = 'log@' + str(platform)
    browser  = 'browser@' + str(platform)
    launcher = 'launcher@' + str(platform) 
    lst_orders     = []
    lst_plnts      = []
    pressLO        = False
    press_plant1   = False
    ordf           = DEFAULT        # Order file picked-up
    plntsel        = DEFAULT_plnts  # plants selected
    uploaded_file  = None
    init_vars(left_gnrlsect, center_gnrlsect,platform)
    #
    directory_log, df_st = setup(platform,log_mach,log,browser,launcher,password)   
    log_st, brw_st = check_agents(log_mach, platform, password, directory_log)
    #
    if platform != DEFAULT_pltfrm:
        shutdown = right_gnrlsect.button('Shutdown')
        st.session_state['shutdown'] = shutdown
        request_agent_list = right_gnrlsect.button('Agent List?')
        st.session_state['req_agnt_lst'] = request_agent_list
    #
    if 'request_agent_list' not in locals():
        request_agent_list = False
    if 'shutdown' not in locals():
        shutdown = False
    #
    if log_st != 1 or brw_st != 1:
        kill_agents(log_mach,directory_log,log_st,brw_st)
        initialize_agents(log_mach, platform, password, directory_log)
    elif request_agent_list:
        directory_log, df_st = setup(platform,log_mach,log,browser,launcher,password)
        st.session_state['req_agnt_lst'] = request_agent_list
        request_agent_list = False                
    #
    df_cnt       = st.container()
    df_container = df_cnt.empty()
    if df_st.shape[0] > 0:
        df_container.dataframe(df_st)
        st.session_state['df_st'] = df_st
    st.session_state['pltfrm'] = platform
    #
    if platform != DEFAULT_pltfrm:
        st.markdown("**_____________________________________________________________________**")
        # 
        # Orders panel (inside the platform)
        vplntsel = False
        if 'current_tab' not in locals():
            old_tab  = ''
        else:
            old_tab  = current_tab
        current_tab = tabs(st,main_tabs)
        if old_tab != current_tab:
            if 'request_agent_list'  in st.session_state:
                request_agent_list = st.session_state['req_agnt_lst']
            if 'shutdown' in st.session_state:
                shutdown = st.session_state['shutdown']
            if 'pltfrm' in st.session_state:
                platform   = st.session_state['pltfrm']
            if 'df_st' in st.session_state:
                df_st      = st.session_state['df_st']
            if 'directory_log' in st.session_state:
                directory_log = st.session_state['directory_log']
            if 'mchn_ordr' in st.session_state:
                machine    = st.session_state['mchn_ordr']
            else:
                machine = DEFAULT_ordrs
            if 'platform' in locals() and 'machine' in locals():
                lst_orders = setup_order(platform,machine)
            if 'uploaded_file' in st.session_state:
                uploaded_file = st.session_state['uploaded_file']
            if platform in st.session_state['mchnvec_ordr']:
                if machine in st.session_state['mchnvec_ordr'][platform]['ords'].keys():
                    ext_ordrs  = st.session_state['mchnvec_ordr'][platform]['ords'][machine]
            #
            if 'OL' in st.session_state:
                if st.session_state['OL'] is not None:
                    pressLO = st.session_state['OL']
            if 'ordf' in st.session_state:
                if st.session_state['ordf'] is not None:
                    ordf = st.session_state['ordf']
            if 'mchn_plnt' in st.session_state:
                plant_mchn = st.session_state['mchn_plnt']
            else:
                plant_mchn = DEFAULT_mchn
            if 'platform' in locals() and 'plant_mchn' in locals():
                lst_plnts  = setup_plant(platform,plant_mchn)
            if 'plntsel' in st.session_state:
                plntsel    = st.session_state['plntsel']
            if platform in st.session_state['mchnvec_plnt']:
                plants_tabs= st.session_state['mchnvec_plnt'][platform]['plnts']
            if 'PS' in st.session_state:
                if st.session_state['PS'] is not None:
                    press_plant1 = st.session_state['PS']
                    plntsel    = st.session_state['plntsel']
    else:
        current_tab = ''
        if 'pltfrm' in st.session_state:
            left_gnrlsect.header('Welcome!')
            left_gnrlsect.write('Here you will manage your Multi-agent System.')
            left_gnrlsect.write('You will be able of keeping track of your agents and bids, their statuses and even uploading order forms and launching them!')
            st.warning('Please, to start the session you need to pick a value')
            center_gnrlsect.image('logo2.png', use_column_width = True)
    #
    if current_tab == 'ORDERS':
        #
        # Seguramente el trabajo en cada región debería encapsularse en una función y
        # usar las variables globales para mantener la lógica y el control ...
        st.empty()
        left_ordr, center_ordr, right_ordr = st.columns((1,2,1))
        machine  = selectbox_with_default(left_ordr,df2['machines'], machine)
        cnt1 = center_ordr.empty()
        rght1= right_ordr.empty()
        if st.session_state['mchn_ordr'] == DEFAULT_ordrs:
            cnt11 = cnt1.write('No Service Machine Selected')
        if st.session_state['mchn_ordr'] != machine and machine != DEFAULT_ordrs: # Change of Machine
            lst_orders = setup_order(platform,machine)
        # Select orders when the machine has been setled up
        if st.session_state['mchn_ordr'] != DEFAULT_ordrs: 
            cnt1 = cnt1.empty()
            uploaded_file = cnt1.file_uploader("Load Orders File", type=['csv'])
        if uploaded_file != None and 'uploaded_file' not in st.session_state:
            ordf = uploaded_file.name
            st.session_state['uploaded_file'] = uploaded_file
            if 'detord' in st.session_state:
                st.session_state.pop('detord')
        ext_ordrs= []
        if platform in st.session_state['mchnvec_ordr'].keys():
            if machine in st.session_state['mchnvec_ordr'][platform]['ords'].keys():
                ext_ordrs= st.session_state['mchnvec_ordr'][platform]['ords'][machine]
        if machine  != DEFAULT_ordrs and ordf not in ext_ordrs:
            detord   =  update_order(platform,machine,log_mach,ordf,uploaded_file)
            if len(detord) > 0:
                rgth1   = right_ordr.empty()                
                rgth11  = rgth1.write('Order Loaded')
                pressLO = rgth1.button('Launch Order')
                if pressLO:
                    rgth1.write('Order being submitted')
                    order_process(platform,machine,detord,ordf,password)
                    pressLO = False
                    rgth11  = rgth1.empty()                  
                    rgth1.write('Order Launched')
                    st.session_state['OL'] = None
                    st.session_state['ordf'] = None
                    directory_log, df_st = setup(platform,log_mach,log,browser,\
                                                launcher,password)
                    if df_st.shape[0] > 0:
                        df_container.empty()
                        df_container.dataframe(df_st)
                        st.session_state['df_st'] = df_st
                    ordf =  DEFAULT
                    st.session_state.pop('detord')
                else:
                    st.session_state['OL'] = pressLO
                    st.session_state['ordf'] = ordf                    
    #
    # Segunda parte
    if current_tab == 'PLANTS':
        st.empty()
        left_plnt, centr_plnt, right_plnt = st.columns((1,2,1))
        plant_mchn = selectbox_with_default(left_plnt,df3['machines'],plant_mchn)
        cnt_plnt   = centr_plnt.empty()
        if st.session_state['mchn_plnt'] != plant_mchn:
            lst_plnts = setup_plant(platform,plant_mchn)
            st.session_state['mchn_plnt'] = plant_mchn
        if st.session_state['mchn_plnt'] == DEFAULT_mchn:
            cnt_plnt.write('No Plant Machine Selected')
        #
        if st.session_state['mchn_plnt'] != DEFAULT_mchn and plntsel == DEFAULT_plnts: 
            cnt_plnt.empty()
            plntsel   = cnt_plnt.selectbox('', optplnts)
            vplntsel  = True
        if plant_mchn != DEFAULT_mchn and plntsel != DEFAULT_plnts:
            if not vplntsel:
                plntsel   = st.session_state['plntsel']
                plntsel   = cnt_plnt.selectbox('', optplnts, \
                                    index = optplnts.index(plntsel))
                vplntsel = True
            if plntsel not in lst_plnts:
                lst_plnts =  update_plant(platform,plant_mchn,log_mach,plntsel)
                rgtha     =  right_plnt.empty()
                rgtha.write('Plant Selected')
                press_plant1 = rgtha.button('Activate Plant')
                if press_plant1:
                    if plant_mchn not in st.session_state['mchnvec_plnt'][platform]['dirs']:
                        setup_plant(platform,plant_mchn)
                    dir_plnts= st.session_state['mchnvec_plnt'][platform]['dirs'][plant_mchn]
                    launch_plant(plntsel,plant_mchn,dir_plnts,platform,log,browser,password)
                    st.session_state['PS']   = None
                    st.session_state['psel'] = None
                    press_plant1 = False
                    directory_log, df_st = setup(platform,log_mach,log,browser,\
                                                launcher,password)
                    if df_st.shape[0] > 0:
                        df_container.empty()
                        df_container.dataframe(df_st)
                        st.session_state['df_st'] = df_st
                    plntsel  = DEFAULT_plnts
                else:
                    st.session_state['PS']   = press_plant1
                    st.session_state['psel'] = plntsel
        if plntsel != DEFAULT_plnts and 'plntsel' not in st.session_state:
            st.session_state['plntsel'] = plntsel            
        if plntsel != DEFAULT_plnts and plntsel != st.session_state['plntsel']:
            st.session_state['plntsel'] = plntsel
    #
    # Thrid part
    if current_tab == 'OUTCOME':
        st.empty()
        left_outcm, centrleft_outcm,right_outcm = st.columns((1,1,3))
        mchn_outcm_list = []
        for machine in st.session_state['mchnvec_ordr'][platform]['ords'].keys():
            mchn_outcm_list.append(machine)
        for mach in st.session_state['mchnvec_plnt'][platform]['plnts'].keys():
            mchn_outcm_list.append(mach)
        list(set(mchn_outcm_list))
        mchn_outcm_list.remove('-- Select Plant Machine --')
        mchn_outcm_list.remove('-- Select Service Machine --')
        outcm_mchn = selectbox_with_default(left_outcm,mchn_outcm_list,DEFAULT_outcm) 
        centrleft_outcm.write(" \
        ")
        #st.session_state['mchnvec_ordr'][platform]['lnos'][machine] ---> list of order codes per machine
        #st.session_state['mchnvec_plnt'][platform]['plnts'][machine]---> list of plants per machine
        if outcm_mchn in st.session_state['mchnvec_ordr'][platform]['ords'].keys() :
            ordr_outcm_list = st.session_state['mchnvec_ordr'][platform]['lnos'][outcm_mchn]
        else:
            ordr_outcm_list = []
        ordr_outcm_list = pd.DataFrame(ordr_outcm_list)
        if outcm_mchn in st.session_state['mchnvec_plnt'][platform]['plnts'].keys() :
            plnt_outcm_list = st.session_state['mchnvec_plnt'][platform]['plnts'][outcm_mchn]
        else:
            plnt_outcm_list = []
        pdb.set_trace()
        if outcm_mchn != DEFAULT_outcm:
            if not(ordr_outcm_list.empty):
                outcm_ordrs = selectbox_with_default(centrleft_outcm,ordr_outcm_list['oname'],DEFAULT_outcm_ordr) 
                if outcm_ordrs != DEFAULT_outcm_ordr:
                    coil_outcm_list = ordr_outcm_list.loc[ordr_outcm_list['oname']==outcm_ordrs, 'cdf']
                    print(coil_outcm_list[:], 'coils list')
                    outcm_coil = 'c009'
                    #outcm_coil = selectbox_with_default(centrleft_outcm,coil_outcm_list,DEFAULT_outcm_coil)
                    ordr_screen, coil_screen = execute_coil(outcm_ordrs, outcm_mchn,outcm_coil, log_mach,directory_log, platform, password)
                    df_ordr_cnt       = right_outcm.container()
                    df__ordr_container = df_ordr_cnt.empty()
                    if ordr_screen.shape[0] > 0:
                        df__ordr_container.dataframe(ordr_screen)
                    if coil_screen.shape[0] > 0:
                        st.dataframe(coil_screen)
                    toutcm_coil = selectbox_with_default(centrleft_outcm,coil_outcm_list,DEFAULT_outcm_coil)
            if len(plnt_outcm_list) >0 :
                outcm_plnt = selectbox_with_default(centrleft_outcm,plnt_outcm_list,DEFAULT_outcm_plnt) 
                if outcm_plnt != DEFAULT_outcm_plnt:
                    right_outcm.write(" ")
                    right_outcm.subheader(outcm_plnt)
                    plnt_screen,server_screen = execute_plant(outcm_plnt, outcm_mchn,log_mach, directory_log,platform,password)
                    df_plnt_cnt       = right_outcm.container()
                    df__plant_container = df_plnt_cnt.empty()
                    if plnt_screen.shape[0] > 0:
                        df__plant_container.dataframe(plnt_screen)
                    if server_screen.shape[0] > 0:
                        st.dataframe(server_screen)
    if shutdown:
        # Si, hay que eliminar las carpetas . De hecho hay que procesar todas
        # las entradas del st.session_state[mchnvec_ordr|mchn_plnt][platform] para 
        # ir borrando procesos y carpetas.
        kill_agents(log_mach,directory_log,1,1)
        #
        for mach in st.session_state['mchnvec_ordr'][platform]['dirs'].keys():
            killall = "rsh "+str(mach)+' "killall python3"'
            out_1 = subprocess.Popen(killall, stdout=None, stdin=None, stderr=None, \
                                close_fds=True, shell=True, universal_newlines = True)
            killall = "rsh "+str(mach)+' " rm -rf tmp*"'
            out_2 = subprocess.Popen(killall, stdout=None, stdin=None, stderr=None, \
                                close_fds=True, shell=True, universal_newlines = True)
        for mach in st.session_state['mchnvec_plnt'][platform]['dirs'].keys():
            killall = "rsh "+str(mach)+' "killall python3"'
            out_1 = subprocess.Popen(killall, stdout=None, stdin=None, stderr=None, \
                                close_fds=True, shell=True, universal_newlines = True)
            killall = "rsh "+str(mach)+' " rm -rf tmp*"'
            out_2 = subprocess.Popen(killall, stdout=None, stdin=None, stderr=None, \
                                close_fds=True, shell=True, universal_newlines = True)
        #reiniciar también session state variables
        restart_vars(platform,log_mach,log, browser, launcher,password)
#
if __name__ == "__main__":
    main()