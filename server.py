import sys,os, subprocess, argparse
import time,datetime, json, math
import tempfile, re, csv, pdb
#
import numpy as np 
import pandas as pd
import streamlit as st
import hydralit as hy
# import streamlit.components.v1 as html
import hydralit_components as hc
#
from pathlib import Path
from  PIL import Image
from dateutil.parser import parse
from urllib.error import URLError
from argparse import ArgumentParser
from ast import literal_eval
from streamlit_option_menu import option_menu
from hydralit.hydra_app import HydraApp
from inspect import trace
#
#
st.set_page_config(
    page_title='UX Industry Process Optimizer',
    page_icon="🖖",
    layout='wide',
    initial_sidebar_state='auto'
)
#
st.markdown("<style>.element-container{opacity:1 !important}</style>", unsafe_allow_html=True)
#
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
    return func(text, np.insert(np.array(values[1:],object),0,default))
#
def get_directory(log_mach):
    oshl = 'ssh '+str(log_mach)+' mktemp -d -p . '
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
    oshl_1 = ' scp agents/*.py @'+str(log_mach)+':'+my_dict + '/'
    res = subprocess.Popen(oshl_1, stdout=subprocess.DEVNULL, stdin=None, \
                        stderr=subprocess.DEVNULL, close_fds=True, shell=True)
    return(my_dict)
#
def initialize_agents(machine, platform, password, my_dict):
    if platform != DEFAULT_pltfrm:
        log     = 'log@' + str(platform)
        browser = 'browser@' + str(platform)
        launcher= 'launcher@' + str(platform)
        ltmp = Path('/tmp/')
        fd,path = tempfile.mkstemp(prefix='tmp_',dir=ltmp)
        fp = os.fdopen(fd,'w')
        # Masking with virtualenv the appropriate releases of python3
        fp.write("#!/bin/bash\n")
        fp.write("python3 --version\ncd $HOME/" + str(my_dict)+'\n')
        fp.write('/usr/bin/nohup python3 ./log.py ' + '-bag '+str(browser) +\
                ' -u '+str(log)+' -p '+password+' -w 900 &\n')
        fp.write('sleep 2\n')
        fp.write('/usr/bin/nohup python3 ./browser.py ' + ' -u '+str(browser)+\
                ' -p '+password+' -lag '+str(log)+ ' -lhg '+str(launcher)+\
                ' -w 900 &\n')
        fp.close()
        #
        oshl = " scp -p " + path + " @" + str(machine) +":" + my_dict + "/agorden.sh"
        err0 = subprocess.Popen(oshl, stdout=subprocess.PIPE, stdin=None, \
                            stderr=subprocess.PIPE, close_fds=True, shell=True)
        lg0, err_0 = err0.communicate()
        #
        oshm = 'ssh ' + str(machine) + ' "'+' dos2unix ' + my_dict + \
                '/agorden.sh ; chmod 0755 ' + my_dict + '/agorden.sh "'
        errm = subprocess.Popen(oshm, stdout=subprocess.DEVNULL, stdin=None, \
                            stderr=subprocess.DEVNULL, close_fds=True, shell=True)
        time.sleep(2)
        #
        oshm2= 'ssh ' + str(machine) + ' "source $HOME/dynreact/bin/activate && /bin/bash ' + \
                    my_dict + '/agorden.sh "'
        errm2= subprocess.Popen(oshm2, stdout=subprocess.DEVNULL, stdin=None, \
                            stderr=subprocess.DEVNULL, close_fds=True, shell=True)
        #
        if err_0.decode() == "":
            os.remove(path)
        else:
            print('Error: ' + err_0.decode() + '->' + lg0.decode())
    return(None)
#
def check_agents(machine, platform, password,my_dict):
    if platform != DEFAULT_pltfrm:
        cmd  = ' "ps aux |grep python3 |grep log.py | grep ' + platform + ' | grep -v grep | wc -l"'
        oshl = 'ssh '+str(machine) + cmd
        out_1= subprocess.Popen(oshl, stdout=subprocess.PIPE, stdin=None, \
                            stderr=subprocess.PIPE, close_fds=True, shell=True)
        logst, err_1 = out_1.communicate()
        #
        cmd  = ' "ps aux |grep python3 |grep browser.py | grep ' + platform + ' | grep -v grep | wc -l"'
        oshl = 'ssh '+str(machine) + cmd
        out_1= subprocess.Popen(oshl, stdout=subprocess.PIPE, stdin=None, \
                            stderr=subprocess.PIPE, close_fds=True, shell=True)
        brwst, err_2 = out_1.communicate()
    else:
        logst= '0'
        brwst= '0'
    #
    return (int(logst),int(brwst))
#
def kill_agents(machine, my_dict,kill_log, kill_brw):
    ltmp = Path('/tmp/')
    fd,path = tempfile.mkstemp(prefix='tmp_',dir=ltmp)
    fp = os.fdopen(fd,'w')
    if kill_brw > 0:
        fp.write("/usr/bin/kill -9 `ps ax |grep browser.py |grep -v grep ")
        fp.write("| awk '{print $1}'`\n")
    if kill_log > 0:
        fp.write("/usr/bin/kill -9 `ps ax |grep log.py |grep -v grep ")
        fp.write("| awk '{print $1}'`\n")
    fp.close()
    if kill_log + kill_brw > 0:
        oshl = " scp " + path + " @" + str(machine) +":" + my_dict + "/klorden.sh"
        err = subprocess.Popen(oshl, stdout=subprocess.DEVNULL, stdin=None, \
                        stderr=subprocess.DEVNULL, close_fds=True, shell=True)
        time.sleep(1)
        oshl1= 'ssh '+str(machine)+ ' "sh ' + str(my_dict) + '/klorden.sh "'
        err = subprocess.Popen(oshl1, stdout=subprocess.PIPE, stdin=None, \
                        stderr=subprocess.PIPE, close_fds=True, shell=True)
        logst, err_1 = err.communicate()
        time.sleep(1)
        oshl2= 'ssh '+str(machine)+ ' "rm -rf ./tmp.*"'
        err = subprocess.Popen(oshl2, stdout=subprocess.DEVNULL, stdin=None, \
                        stderr=subprocess.DEVNULL, close_fds=True, shell=True)
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
            olcs = "ssh " + str(j) + "  ps -ax | grep coil.py | grep '"
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
            olcs = "ssh "+str(j)+" ps -ax | grep python3 | grep "+rdir
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
def list_snapshots(pltf,lstplts):
    olcs = "ssh "+pltf+" ls -1t *Snapshot*.csv"
    out  = subprocess.Popen(olcs, stdout=subprocess.PIPE, stdin=None, \
                                stderr=subprocess.PIPE,close_fds=True, shell=True, \
                                universal_newlines = True)
    outlst, err = out.communicate()
    lst_objs    = outlst.rstrip().split('\n')
    ntpdt = pd.DataFrame()
    #
    if len(';'.join(lst_objs)) > 0:
        ltmp = Path('/tmp/')
        fd,path = tempfile.mkstemp(prefix='tmp_',dir=ltmp)
        os.close(fd)
        orgf = lst_objs[0].replace(' ','*').replace('(','*').replace(')','*')
        oshl = " scp @" + pltf +':"'+ orgf + '" ' + path
        err2 = subprocess.Popen(oshl, stdout=subprocess.PIPE, stdin=None, \
                        stderr=subprocess.PIPE, close_fds=True, shell=True)
        outlst2, err_2 = err2.communicate()
        time.sleep(5)
        try:
            tmpdt= pd.read_csv(path,sep=';', index_col=False, encoding='utf-8',
                            header= 0, decimal=',',low_memory=False)
            tmpdt['Present Plant'] = tmpdt['Present Plant'].str.replace('VEA','VA')
            ntpdt= tmpdt.loc[tmpdt['Present Plant'].isin(lstplts)]
        except FileNotFoundError:
            print("File {} not found.".format(path))
        except pd.errors.EmptyDataError:
            print("File {} has No data".format(path))
        except pd.errors.ParserError:
            print("File {} Parse error".format(path))
        except Exception as e:
            print("Some other exception")
            raise e
        os.remove(path)
    return({'rfiles':lst_objs,'snap':ntpdt})
#
def list_lots(snap,tgplnts):
    res  = {}
    if snap.shape[0] > 0:
        lidx =[item for item in snap['Lot ID'].unique().tolist() if str(item) != 'nan' ]
        for i in lidx:
            tmp = snap.loc[snap['Lot ID']==i,'Production Order NR'].unique().tolist()
            res[i] = tmp
    return(res)
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
def launch_orders(fp,detorder, my_dict, platform, password):
    #
    log = 'log@' + str(platform)
    browser = 'browser@' + str(platform)
    launcher = 'launcher@' + str(platform)
    for i in detorder['cdf'].loc[:,'CoilName'].tolist(): 
        st.session_state['mchnvec_ordr'][platform]['clts'].append(i)
    cnames  = ['c'+j for j in detorder['cdf'].loc[:,'CoilName'].tolist()]
    lst_cns = ','.join(cnames)
    lst_pss = ','.join(detorder['cdf'].loc[:,'PltSource'].tolist())
    lst_lgth= ','.join([str(int(k)) for k in detorder['cdf'].loc[:,'CoilLength'].tolist()])
    fp.write("\n/usr/bin/nohup /usr/bin/python3 " + str(my_dict)+ "/launcher.py ")
    fp.write("-oc '"+str(detorder['oname'])+"' -sg '"+str(detorder['mat']))
    fp.write("' -at "+str(detorder['thick'])+ " -wi "+str(int(detorder['width'])))
    fp.write(" -ag "+str(detorder['ag'])+ " -asn "+str(int(detorder['asn'])))
    fp.write(" -os "+str(int(detorder['os'])) + " -sr "+str(int(detorder['sr'])))
    fp.write(" -sd '" + detorder['dued'] + "'")
    fp.write(" -nc "+str(detorder['ncls'])+" -lc '" + lst_cns + "' -po ")
    fp.write(str(int(detorder['bdgt'])) + " -lp \'" + lst_pss + "\' -ll \'")
    fp.write(lst_lgth + "' -so '" + detorder['prule'].replace(')','\)').replace('(','\('))
    fp.write("' -bag " + str(browser) + " -lag " + str(log) + " -u ")
    fp.write(str(launcher)+" -p "+password+" -w 40 &\n")
    return(None)
#
def check_remote(machine,platform):
    key1 = 'mchnvec_plnt'
    key2 = 'mchnvec_ordr'
    if not machine in st.session_state[key1][platform]['dirs'].keys(): # Needed new scp
        if not machine in st.session_state[key2][platform]['dirs'].keys(): # Needed new scp
            tgdirs = turn_on_systm(machine)
            st.session_state[key1][platform]['dirs'][machine] = tgdirs
        else:
            st.session_state[key1][platform]['dirs'][machine]= \
                   st.session_state[key2][platform]['dirs'][machine]
    return(st.session_state[key1][platform]['dirs'][machine])
#
def launch_plant(plant, machine, my_dict, platform, log, browser, password):
    if plant in st.session_state['mchnvec_plnt'][platform]['plnts'][machine]:
        return(None)
    if platform != DEFAULT_pltfrm:
        va = str(plant.lower())+'@' + str(platform)
        ltmp = Path('/tmp/')
        fd,path = tempfile.mkstemp(prefix='tmp_',dir=ltmp)
        fp = os.fdopen(fd,'w')
        fp.write("#! /bin/bash\n\n#. $HOME/dynreact/bin/activate\n\n")            
        fp.write("\ncd " + str(my_dict)+ "\n")
        fp.write("/usr/bin/nohup /usr/bin/python3 $HOME/"+ str(my_dict)+"/va.py ")
        fp.write("-an '"+str(int(plant[-2:]))+"' -sd '"+str(0.25))
        fp.write("' -bag " + str(browser) + " -lag " + str(log) + " -u ")
        fp.write(str(va)+" -p "+password+" &\n")
        fp.close()
        oshl = " scp -p "+path+" @"+str(machine)+":\$HOME/"+my_dict+"/lchplanta.sh"
        err0 = subprocess.Popen(oshl, stdout=subprocess.DEVNULL, stdin=None, \
                            stderr=subprocess.DEVNULL, close_fds=True, shell=True)
        oshl1= 'ssh '+str(machine)+ ' "sh ' + str(my_dict) + '/lchplanta.sh"'
        time.sleep(1)
        err1 = subprocess.Popen(oshl1, stdout=subprocess.DEVNULL, stdin=None, \
                            stderr=subprocess.DEVNULL, close_fds=True, shell=True)
        os.remove(path)
        if plant not in st.session_state['mchnvec_plnt'][platform]['plnts'][machine]:
            st.session_state['mchnvec_plnt'][platform]['plnts'][machine].append(plant)
    return(None)
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
def init_vars(platform):
    if 'directory_log' not in st.session_state:
        st.session_state['directory_log']= None
    if 'sellots' not in st.session_state:
        st.session_state['sellots']      = []
    if 'lotsOK' not in st.session_state:
        st.session_state['lotsOK']      = None
    if 'pltfrm' not in st.session_state:
        st.session_state['pltfrm']       = None
    if 'pltvec' not in st.session_state:
        st.session_state['pltvec']       = {}
    if 'plntsel' not in st.session_state:
        st.session_state['plntsel'] = []
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
    if 'tgplnts' not in st.session_state:
        st.session_state['tgplnts'] = []
    return(None)
#
def setup(center_gnrlsect,platform,log_mach,log, browser, launcher,password):
    df_st = pd.DataFrame()
    directory_log = ''
    if platform in st.session_state['mchnvec_ordr'].keys() :
        directory_log = st.session_state['mchnvec_ordr'][platform]['pltd']
    elif platform != DEFAULT_pltfrm:
        directory_log = turn_on_systm(log_mach)
        #  Machine on the Order section
        st.session_state['mchnvec_ordr'][platform] = {}
        st.session_state['mchnvec_ordr'][platform]['srvn'] = log_mach # machine for log/browser
        st.session_state['mchnvec_ordr'][platform]['pltd'] = directory_log # directory for log/browser in log_mach       
        st.session_state['mchnvec_ordr'][platform]['ords'] = {} # list of files per machine
        st.session_state['mchnvec_ordr'][platform]['lnos'] = {} # list of order codes per machine
        st.session_state['mchnvec_ordr'][platform]['dirs'] = {} # directory per machine
        st.session_state['mchnvec_ordr'][platform]['clts'] = [] # list of coils machine
        st.session_state['mchnvec_ordr'][platform]['lots'] = {} # list of lots        
        #  Machine on the Plant section
        st.session_state['mchnvec_plnt'][platform] = {}
        st.session_state['mchnvec_plnt'][platform]['srvn'] = log_mach # machine for log/browser
        st.session_state['mchnvec_plnt'][platform]['pltd'] = directory_log # directory for log/browser in log_mach
        st.session_state['mchnvec_plnt'][platform]['plnts']= {}
        st.session_state['mchnvec_plnt'][platform]['dirs'] = {} # directory per machine
        st.session_state['mchnvec_plnt'][platform]['clts'] = [] # list of plants machine
        # st.session_state['mchnvec_plnt'][platform]['lots'] = {} # list of lots
    if len(directory_log) > 0:
        st.session_state['directory_log'] = directory_log
    if platform != DEFAULT_pltfrm:
        st.session_state['pltfrm'] = platform
        with center_gnrlsect:
            res   = display_table(platform, log_mach, log, browser, launcher, \
                                directory_log, password)
            df_list_plnts = res['lpts']
            df_list_coils = res['lcls']
            df_st = res['df']
            if df_st.shape[0] > 0:
                df_st.set_index('Selected platform',inplace=True) 
    return(directory_log, df_st)
#
def restart_vars(centr,platform,log_mach,log, browser, launcher,password):
    st.session_state['directory_log']= None
    st.session_state['pltfrm']       = None
    st.session_state['pltvec']       = {}
    st.session_state['mchn_ordr']    = DEFAULT_ordrs
    st.session_state['mchnvec_ordr'] = {}
    st.session_state['mchn_plnt']    = DEFAULT_mchn
    st.session_state['mchnvec_plnt'] = {}
    st.session_state['areaordrs']    = None
    st.session_state['lotsOK']       = None
    st.session_state['sellots']      = []
    #
    x,y = setup(centr,platform,log_mach,log, browser, launcher,password)
    return(None)
#
def setup_order(platform,machine):
    if machine in st.session_state['mchnvec_ordr'][platform]['ords'].keys() :
        lst_orders = st.session_state['mchnvec_ordr'][platform]['ords'][machine]
    else:
        lst_orders = []
        ord_dir    = turn_on_systm(machine)
        st.session_state['mchnvec_ordr'][platform]['ords'][machine] = lst_orders
        st.session_state['mchnvec_ordr'][platform]['lnos'][machine] = []
        st.session_state['mchnvec_ordr'][platform]['lots'][machine] = []
        st.session_state['mchnvec_ordr'][platform]['dirs'][machine] = ord_dir
        # st.session_state['mchnvec_ordr'][platform]['clts'].append(machine)
    st.session_state['mchn_ordr'] = machine
    return(lst_orders)
#
def order_process(platform,machine,dctcoils,sellots,optplnts,password):
    #lanzar órdenes
    lst_orders = setup_order(platform,machine)
    dir_orders = st.session_state['mchnvec_ordr'][platform]['dirs'][machine]
    dfcoils = dctcoils['snap']
    ltmp = Path('/tmp/')
    fd,path = tempfile.mkstemp(prefix='tmp_',dir=ltmp)
    fp = os.fdopen(fd,'w')
    fp.write("#!/bin/bash\n\n#. $HOME/dynreact/bin/activate\n\n")
    # pdb.set_trace()
    for ilt in sellots:
        ordfs = dfcoils.loc[dfcoils['Lot ID']==ilt,'Production Order NR'].unique()
        for ird in ordfs:
            mat = dfcoils.loc[dfcoils['Production Order NR']==ird,'Steelgrade'].unique()[0]
            thk = dfcoils.loc[dfcoils['Production Order NR']==ird,'Final Thickness (mm)'].unique()[0]
            wid = dfcoils.loc[dfcoils['Production Order NR']==ird,'Final Width (mm)'].unique()[0]
            pry = dfcoils.loc[dfcoils['Production Order NR']==ird,'Lot Priority (Text)'].unique()[0]
            arg = dfcoils.loc[dfcoils['Production Order NR']==ird,'Article Group'].unique()[0]
            # lct = dfcoils.loc[dfcoils['Production Order NR']==ird,'Location Field'].unique()[0]
            ols = dfcoils.loc[dfcoils['Production Order NR']==ird,'Oil Layer'].unique()[0]
            sdrr= dfcoils.loc[dfcoils['Production Order NR']==ird,'Reduction Rate'].unique()[0]
            sdr = 1
            if float(sdrr) < 4. :
                sdr = 0
            asn = dfcoils.loc[dfcoils['Production Order NR']==ird,'Passivation'].unique()[0]
            ddat= parse(dfcoils.loc[dfcoils['Production Order NR']==ird,'Delivery Date Day'].unique()[0])
            sdat= ddat.strftime("%Y-%m-%d")
            ncls= dfcoils[dfcoils['Production Order NR']==ird].shape[0]
            if isinstance(pry,str):
                try:
                    pry = int(pry)
                except:
                    pdb.set_trace()
            if math.isnan(pry):
                pry = 0.1
            splt= ''
            for iplt in optplnts:  # Sometimes Plants are named VA* or VEA*
                ncol = iplt[0:1]+'E'+iplt[1:]+'-Performance (t/h)'
                pltac= dfcoils.loc[dfcoils['Production Order NR']==ird,ncol].unique()[0]
                if pltac == 1:
                    splt = splt + '|' + iplt
            splt = '(' + splt[1:] + ')' # Regular expression of interesting plants
            lcls = dfcoils.loc[dfcoils['Production Order NR']==ird,['MatID','Location Field']].copy()
            # Setup of defaults values because there are lots of NaNs
            dfcoils.loc[dfcoils['Production Order NR']==ird,'Final Thickness (mm)'] = \
                dfcoils.loc[dfcoils['Production Order NR']==ird,'Final Thickness (mm)'].replace(np.nan, 0.3)
            dfcoils.loc[dfcoils['Production Order NR']==ird,'Final Width (mm)'] = \
                dfcoils.loc[dfcoils['Production Order NR']==ird,'Final Width (mm)'].replace(np.nan, 900.)
            #
            lcls['CoilLength'] = 1.e+6 * dfcoils.loc[dfcoils['Production Order NR']==ird,'Weight (t)'] / \
                            (dfcoils.loc[dfcoils['Production Order NR']==ird,'Final Thickness (mm)']*\
                             dfcoils.loc[dfcoils['Production Order NR']==ird,'Final Width (mm)']*7850)
            lcls.columns    = ["CoilName","PltSource","CoilLength"]
            lcls['CoilName']= lcls['CoilName'].astype(str)
            detord= {'oname':str(ird),'mat':str(mat),'thick':thk,'width':wid,'bdgt':2000*pry*ncls,\
                    'dued': sdat,'prule':splt,'ncls':ncls,'cdf':lcls,'ag':arg,\
                    'os':ols,'sr':sdr,'asn':asn}
            launch_orders(fp,detord,dir_orders,platform,password)                    
            st.session_state['mchnvec_ordr'][platform]['ords'][machine].append(ird)
            st.session_state['mchnvec_ordr'][platform]['lnos'][machine].append(detord)
            st.session_state['mchnvec_ordr'][platform]['lots'][machine].append(ilt)    
    #
    fp.close()
    oshl = " scp " + path + " @" + str(machine) +":" + dir_orders + "/lchorden.sh"
    err0 = subprocess.Popen(oshl, stdout=subprocess.DEVNULL, stdin=None, \
                        stderr=subprocess.DEVNULL, close_fds=True, shell=True)
    oshl1= ' ssh '+str(machine)+' " dos2unix ' + str(dir_orders) + '/lchorden.sh ; sh ' +\
            str(dir_orders) + '/lchorden.sh"'
    time.sleep(2)
    err1 = subprocess.Popen(oshl1, stdout=subprocess.DEVNULL, stdin=None, \
                        stderr=subprocess.DEVNULL, close_fds=True, shell=True)
    os.remove(path)
    time.sleep(18)
    return(None)
#
# JOM removed: read_log_for_coil & read_log_for_plant
# JOM replacement: 
def recovery_log(platform,verbose,remote):
    if platform in st.session_state['mchnvec_plnt']:
        if remote: # Collecting the log.log from remote machine
            directory_log = st.session_state['mchnvec_plnt'][platform]['pltd']
            machine       = st.session_state['mchnvec_plnt'][platform]['srvn']
            ltmp = Path('/tmp/')
            fd,path = tempfile.mkstemp(prefix='log_',dir=ltmp)
            oshl =  " scp -p " + " @" + str(machine) +":" + directory_log + \
                    "/log.log " + path
            err0 = subprocess.Popen(oshl, stdout=subprocess.PIPE, stdin=None, \
                                stderr=subprocess.PIPE, close_fds=True, shell=True)
            comm, err_1 = err0.communicate()
            st.session_state['lpath'] = path
        #
        path = st.session_state['lpath']
        if len(path) == 0:
            if verbose:
                print("No remote log.log requested but local copy doesn't exist")
            return None 
        pdb.set_trace()
        lgf  = pd.read_csv(path,sep=';',header=None)
        lgf.columns = ['dtime','type','Agnt','Carrier','metadata']
        lgf['dtime'] = pd.to_datetime(lgf['dtime'])
        lgf  = lgf.loc[lgf['metadata'].str.len() > 2,:]
        lgf['dict']  = lgf['metadata'].apply(json.loads)
        idx  = lgf['dict'].apply(lambda x: 'Profit' in x[0].keys())
        idxu = lgf.loc[idx].index[lgf['dict'].loc[idx].apply(len).argmax()]
        rst  = pd.DataFrame(lgf['dict'].loc[idxu])
        return({'mainlog':lgf,'metadata':rst, 'idxres':idxu})
    else:
        return None
#
def auctions_log(lgs,mdt):
    def sjf(s):
        ss = s.split(',')
        ss = [j.strip() for j in ss]
        lss= []
        for iss in ss:
            if 'by' in iss:
                jss = iss.replace('by: ','"by":"')+'"'
            else:
                jss = '"'+iss.replace(' ','').replace(':','":"').replace(',','","')+'"'
            lss.append(jss)
        scn= ','.join(lss)
        t  = '{'+scn+'}'
        return(t)
    #
    res = pd.DataFrame()
    sbs  = pd.DataFrame()
    idx1 = mdt.loc[:,'location_2'].notnull()
    if idx1.sum() > 0:
        lbls = ['auction_number','coil_auction_winner','location','location_1','location_2', \
                'ship_date','coil_length','coil_width','coil_thickness','bid','budget','Profit',\
                'idxold']
        sbs  = mdt.loc[idx1,lbls]
    idx2 = mdt['msg'].notnull()
    if idx2.sum() > 0:
        mdt2 = mdt.loc[idx2,'msg']
        idx3 = mdt2.str.contains('ENDEDUP')
        # 
        # to extract cost structure ... and glue it in the records
        sdt3 = mdt2.loc[idx3].apply(sjf)
        sdt4 = pd.DataFrame()
        for idx4 in sdt3.index:
            dmd = json.loads(sdt3.loc[idx4])
            pd0 = pd.DataFrame(dmd,index=[idx4])
            sdt4= pd.concat([sdt4,pd0], axis=0)
            res = sbs.merge(sdt4,left_on='coil_auction_winner',right_on='ENDEDUP')
        res['auction_number'] = res['auction_number'].astype(int)
        res.index = sbs.index
    return(res)
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
    lastlog_date    = None     # Holding the date of the last log.log recovery process
    platforms_parser.append(DEFAULT_pltfrm)
    platforms_parser.sort()
    df        = pd.DataFrame({
        'apiict': platforms_parser})
    df2       = pd.DataFrame({
        'machines': machines_parser})
    yes_no    = pd.DataFrame({
        'check': ['Yes', 'No']})
    df3       = df2
    #
    # specify the primary menu definition
    menu_data = [
        {'id':'ORDERS','icon': "envelope", 'label':"ORDERS"},
        {'id':'PLANTS','icon':"building",'label':"PLANTS"},
        {'id':'OUTCOME','icon': "far fa-chart-bar", 'label':"OUTCOME"},
    ]
    menu_style = {
                "container": {"padding": "5!important", "background-color": "#ffffff"},
                "icon": {"color": "blue", "font-size": "20px"}, 
                "nav-link": {"font-size": "13px", "text-align": "left", "margin":"0px", "--hover-color": "#ADD8E6"},
                "nav-link-selected": {"background-color": "#ADD8E6"},
                }
    #
    # main_tabs = ['ORDERS','PLANTS','OUTCOME']
    optplnts  = ['VA08','VA09','VA10','VA11','VA12','VA13']
    tgplnts   = []
    if 'optg' not in locals():
        optg={}
    if 'sellots' not in locals():
        sellots={}
    if 'lhplnts' not in locals():
        lhplnts={}
    # 
    # pdb.set_trace()
    if 'placeholder' not in st.session_state.keys():
        placeholder    = st.empty()
        st.session_state['placeholder'] = placeholder    
    title_container= st.container()
    #
    left_gnrlsect, center_gnrlsect, right_gnrlsect = title_container.columns((2,4,1))
    left_gnrlsect.image('logo.png', width=128)
    #
    lst_orders     = []
    lst_plnts      = []
    pressLO        = False
    press_plant1   = False
    ordf           = DEFAULT        # Order file picked-up
    plntsel        = DEFAULT_plnts  # plants selected
    uploaded_file  = None
    #
    try:
        platform = st.session_state['pltfrm']
    except:
        if 'platform' not in locals(): 
            platform = DEFAULT_pltfrm
            st.session_state['pltfrm'] = platform
    if 'request_agent_list' not in locals():
        request_agent_list = False
    if 'shutdown' not in locals():
        shutdown = False
    #
    if platform == DEFAULT_pltfrm:
        current_tab = ''
        center_gnrlsect.write('**Select the targeted plant(s)**')
        if sum(v for k,v in optg.items()) == 0:
            for itg in range(len(optplnts)):
                optg[itg] = center_gnrlsect.checkbox(optplnts[itg])
            # optg = center_gnrlsect.multiselect('Select one or more options',optplnts)
        #
        center_gnrlsect.write('\n\n**Select the interesting negotiating sites**')
        platform = selectbox_with_default(center_gnrlsect, df['apiict'], \
                                        DEFAULT_pltfrm, "Platform:")
        #
        log      = 'log@' + str(platform)
        browser  = 'browser@' + str(platform)
        launcher = 'launcher@' + str(platform)
        #
        center_gnrlsect.write('\n')
        left_gnrlsect.header('Welcome!')
        left_gnrlsect.write('Here you will manage your Multi-agent System.')
        left_gnrlsect.write('You will be able of keeping track of your agents and bids, their statuses and even uploading order forms and launching them!')
        # st.warning('Please, to start the session you need to pick a the plant(s) and the platform in this order')
        center_gnrlsect.image('logo2.png', use_column_width = True)
        center_gnrlsect.write('\n\n\n\n')
        original_warning =  '<p style="font-family:Courier; color:Red; font-size: 20px;">' + \
                            '<b><it>Please, to start the session you need to pick the plant(s) ' + \
                            'and the platform in this order</it></b>'
        center_gnrlsect.markdown(original_warning, unsafe_allow_html=True)
        #
        if platform != st.session_state['pltfrm']:
            for itg in range(len(optplnts)):
                if optg[itg] == 1:
                    tgplnts.append(optplnts[itg])
            lstsnapsh = list_snapshots(platform,tgplnts)
            st.session_state['snapshot'] = lstsnapsh
            lstlots   = list_lots(lstsnapsh['snap'],tgplnts)
            st.session_state['lots'] = lstlots
            st.session_state['pltfrm'] = platform
            st.session_state['tgplnts']= tgplnts
            # pdb.set_trace()
            # 
            # Setup of contexts ... gathered from 766 lines
            log      = 'log@' + str(platform)
            browser  = 'browser@' + str(platform)
            launcher = 'launcher@' + str(platform)
            init_vars(platform)
            directory_log, df_st = setup(center_gnrlsect,platform,log_mach, \
                                        log,browser,launcher,password)
            st.session_state['directory_log'] = directory_log
            st.session_state['df_st'] = df_st
            srvplnt   = st.session_state['mchnvec_plnt'][platform]['srvn']
            #
            st.session_state['placeholder'].empty()
            placeholder    = st.empty()
            title_container= st.container()
            left_gnrlsect, center_gnrlsect, right_gnrlsect = title_container.columns((2,4,1))
            left_gnrlsect.image('logo.png', width=128)
            st.session_state['placeholder'] = placeholder
        #
    if platform != DEFAULT_pltfrm:
        log      = 'log@' + str(platform)
        browser  = 'browser@' + str(platform)
        launcher = 'launcher@' + str(platform)         
        # init_vars(platform)
        if 'directory_log' in st.session_state:
            directory_log = st.session_state['directory_log']
            df_st         = st.session_state['df_st']
            log_st, brw_st= check_agents(log_mach, platform, password, directory_log)
        #
        # Setting interaction buttons.
        shutdown = right_gnrlsect.button('Shutdown')
        st.session_state['shutdown'] = shutdown
        request_agent_list = right_gnrlsect.button('Agent List?')
        st.session_state['req_agnt_lst'] = request_agent_list
        #
        if log_st != 1 or brw_st != 1: # If both are 1, platform and agents are running.
            kill_agents(log_mach,directory_log,log_st,brw_st)
            initialize_agents(log_mach, platform, password, directory_log)
            log_st, brw_st = check_agents(log_mach, platform, password, directory_log)
            ltmp = Path('/tmp/')
            fd,path = tempfile.mkstemp(prefix='tmp_',dir=ltmp)
            st.session_state['pltvec'][platform] = {}
            st.session_state['pltvec'][platform]['local_log'] = path
        elif request_agent_list:
            directory_log, df_st = setup(center_gnrlsect,platform,log_mach,log,browser,launcher,password)
            st.session_state['req_agnt_lst'] = request_agent_list
            request_agent_list = False
            ltmp = Path('/tmp/')
            fd,path = tempfile.mkstemp(prefix='tmp_',dir=ltmp)
            st.session_state['pltvec'][platform] = {}
            st.session_state['pltvec'][platform]['local_log'] = path   
        #
        if df_st.shape[0] > 0:
            st.session_state['df_st'] = df_st
            st.markdown("**_____________________________________________________________________**")            
        #
        #
        #
        vplntsel = False
        if 'current_tab' not in locals():
            old_tab  = ''
        else:
            old_tab  = current_tab
        #
        over_theme = {'txc_inactive': '#ffffff'}
        current_tab = hc.nav_bar(
            menu_definition=menu_data,
            override_theme=over_theme,
            home_name='Home',
            # login_name='Logout',
            hide_streamlit_markers=False, #will show the st hamburger as well as the navbar now!
            sticky_nav=True, #at the top or not
            sticky_mode='pinned', #jumpy or not-jumpy, but sticky or pinned
            )
        #
        #get the id of the menu item clicked --> current_tab
        #
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
            #
            if 'mchn_plnt' in st.session_state:
                plant_mchn = st.session_state['mchn_plnt']
            else:
                plant_mchn = DEFAULT_mchn
            #if 'platform' in locals() and 'plant_mchn' in locals():
            #     lst_plnts  = setup_plant(platform,plant_mchn)
            if 'plntsel' in st.session_state:
                plntsel    = st.session_state['plntsel']
            if platform in st.session_state['mchnvec_plnt']:
                plants_tabs= st.session_state['mchnvec_plnt'][platform]['plnts']
            if 'PS' in st.session_state:
                if st.session_state['PS'] is not None:
                    press_plant1 = st.session_state['PS']
                    plntsel    = st.session_state['plntsel']
    #
    if current_tab == 'Home':
        # st.write(st.session_state['mchn_ordr'], 'Order')
        # st.write(st.session_state['mchn_plnt'], 'Plant')
        df_cnt       = st.container()
        df_container = df_cnt.empty()
        try:
            df_st = st.session_state['df_st']
        except:
            df_st = pd.DataFrame()
        if df_st.shape[0] > 0:
            df_container.dataframe(df_st)
    #
    if current_tab == 'ORDERS':
        #
        # Seguramente el trabajo en cada región debería encapsularse en una 
        # función y usar las variables globales para mantener la lógica y el control ...
        st.empty()
        left_ordr, center_ordr, right_ordr = st.columns((1,2,1))
        df_cnt = center_ordr.container()
        df_container = df_cnt.empty()
        # st.markdown("**_____________________________________________________________________**")
        try:
            df_st = st.session_state['df_st']
        except:
            st.warning("Error: DF_ST not defined")
        #
        df_container.dataframe(df_st)
        with left_ordr:
            machine = option_menu("Machines:", options = machines_parser,
                                    default_index = 0,
                                    menu_icon="cast",
                                    styles=menu_style)
        #
        # if st.session_state['mchn_ordr'] == DEFAULT_ordrs:
        rght1= right_ordr.empty()
        #
        right_ordr.write(':'.join(tgplnts))
        #
        if st.session_state['mchn_ordr'] == DEFAULT_ordrs:
            cnt1 = df_cnt.write('No Service Machine Selected')
            st.session_state['mchn_ordr'] = machine
        if st.session_state['mchn_ordr'] != DEFAULT_ordrs: # Machine for orders selected 
            df_cnt.write(' ')
            lstlots = list(st.session_state['lots'].keys())
            new_lbl = '<p style="font-family:sans-serif; color:Blue; font-size: 24px;">Select the relevant Lots to be scheduled</p>'
            df_cnt.markdown(new_lbl, unsafe_allow_html=True)
            for itg in range(len(lstlots)):
                if lstlots[itg] not in st.session_state['sellots']:
                    sellots[itg] = df_cnt.checkbox(lstlots[itg])
                else:
                    sellots[itg] = False
            df_cnt.write(' ')
            if machine in st.session_state['mchnvec_ordr'][platform]['ords']: 
                rgth1   = right_ordr.empty()
                rgth1.write('Order(s) already submitted:')
                right_ordr.write(st.session_state['mchnvec_ordr'][platform]['ords'][machine])
            if df_cnt.button('Submit Lots(orders) for Scheduling'):
                st.session_state['OL'] = 1
                rgth1   = right_ordr.empty()
                rgth1.write('Order(s) being submitted')
                for itg in range(len(lstlots)):
                    if sellots[itg] and lstlots[itg] not in \
                                            st.session_state['sellots']:
                        st.session_state['sellots'].append(lstlots[itg])               
                order_process(platform,machine,st.session_state['snapshot'], \
                                st.session_state['sellots'],optplnts,password)
                rgth1.write('Order(s) submitted')
                right_ordr.write(st.session_state['mchnvec_ordr'][platform]['ords'][machine])
                st.session_state['OL'] =None
        # pdb.set_trace()
    # 
    if current_tab == 'PLANTS':
        st.empty()
        left_plnt, centr_plnt, right_plnt = st.columns((1,2,1))
        df_cnt = centr_plnt.container()
        df_container = df_cnt.empty()
        # st.markdown("**_____________________________________________________________________**")
        try:
            df_st = st.session_state['df_st']
        except:
            st.warning("Error: DF_ST not defined")
        #
        df_container.dataframe(df_st)
        with left_plnt:
            plant_mchn = option_menu("Plant Selection", options = machines_parser,
                                    default_index = 0, menu_icon="minecart",
                                    styles=menu_style)
        # plant_mchn = selectbox_with_default(left_plnt,df3['machines'],plant_mchn)
        if st.session_state['mchn_plnt'] != plant_mchn:
            st.session_state['mchn_plnt'] = plant_mchn
        if st.session_state['mchn_plnt'] == DEFAULT_mchn:
            df_cnt.write('No Plant Machine Selected')
        #
        lst_plnts = st.session_state['tgplnts']
        if st.session_state['mchn_plnt'] != DEFAULT_mchn: 
            df_cnt.write(' ') 
            new_lbl2= '<p style="font-family:sans-serif; color:Blue; font-size: 24px;">Select the relevant Plants to be scheduled</p>'
            df_cnt.markdown(new_lbl2, unsafe_allow_html=True)
            for itp in range(len(lst_plnts)):
                if lst_plnts[itp] not in st.session_state['plntsel']:
                    lhplnts[itp] = df_cnt.checkbox(lst_plnts[itp])
                else:
                    lhplnts[itp] = False
            df_cnt.write(' ')
            #
            rgtha     =  right_plnt.empty()
            rgtha.write('Plant Selection')
            if df_cnt.button('Activate Plant(s)'):
                rgth1 = right_plnt.empty()
                rgth1.write('Plant(s) being submitted')
                dir_plnts = check_remote(plant_mchn,platform) 
                for itp in range(len(lst_plnts)):
                    if lhplnts[itp] and lhplnts[itp] not in \
                                            st.session_state['plntsel']:
                        st.session_state['plntsel'].append(lst_plnts[itp])
                        if not plant_mchn in st.session_state['mchnvec_plnt'][platform]['plnts'].keys():
                            st.session_state['mchnvec_plnt'][platform]['plnts'][plant_mchn] = []
                        launch_plant(lst_plnts[itp],plant_mchn,dir_plnts,platform,log, \
                                     browser,password)
                rgth1.write('Plant(s) started:')
                right_plnt.write(st.session_state['mchnvec_plnt'][platform]['plnts'][plant_mchn])
                dir_plnts= st.session_state['mchnvec_plnt'][platform]['dirs'][plant_mchn]
    # Third part
    if current_tab == 'OUTCOME':
        st.empty()
        left_outcm, centrleft_outcm,right_outcm = st.columns((1,1,3))
        df_seleplnt_cnt= left_outcm.container()
        df_seleordr_cnt= centrleft_outcm.container()
        df_selecoil_cnt= right_outcm.container()
        df_cnt_1 = df_seleplnt_cnt.empty()
        df_cnt_2 = df_seleordr_cnt.empty()
        df_cnt_3 = df_selecoil_cnt.empty()
        #extraer TODAS las plantas activas
        plnt_list = ['Select a Plant']
        ordr_list = ['Select an Order']
        # pdb.set_trace()
        for mach in st.session_state['mchnvec_plnt'][platform]['plnts'].keys():
            for i in st.session_state['mchnvec_plnt'][platform]['plnts'][mach]: 
                plnt_list.append(i)
        for mach in st.session_state['mchnvec_ordr'][platform]['ords'].keys():
            for j in st.session_state['mchnvec_ordr'][platform]['lnos'][mach]: 
                ordr_list.append(j['oname'])
        plnt_outcm_list = list(set(plnt_list))
        ordr_outcm_list = list(set(ordr_list))    
        # We check the last date for the log.log file
        if 'lastlog_date' in st.session_state:
            lastlog_date = st.session_state['latlog_date']
        else:
            lastlog_date = datetime.datetime.now()
        if (datetime.datetime.now() - lastlog_date).total_seconds() > 120:
            tmpres = recovery_log(platform,True,True)
            if tmpres:
                st.session_state['lastlog_date']= datetime.datetime.now()
        else: # Without remote copy of log.log
            tmpres = recovery_log(platform,True,False)
        if tmpres:
            loga = tmpres['mainlog']
            logb = tmpres['metadata']
            pdb.set_trace()
            sbst = auctions_log(loga,logb)
        # Proceed with menus
        with df_cnt_1:
            plnt_selection = option_menu("Plant Selection", plnt_outcm_list,
                                default_index = 0, menu_icon="building",
                                styles=menu_style)
        if plnt_selection != 'Select a Plant':
            pdb.set_trace()
            df_cnt_3.table(sbst.loc[:,['auction_number','code','coil_width',\
                               'coil_thichness','order','offer','Profit']])
            df_cnt_3.write('----')
            with df_cnt_2:
                ordr_selection = option_menu("Order Selection", ordr_outcm_list,
                                    default_index = 0, menu_icon="envelope",
                                    styles=menu_style)
                pdb.set_trace()
                if ordr_selection != 'Select an Order':
                    df_cnt_3.table(sbst.loc[sbst.order==ordr_selection,:])
            with df_cnt_3: 
                op_coil_outcm = ['Select '+DEFAULT_outcm_coil] + \
                            st.session_state['mchnvec_ordr'][platform]['clts']
                coil_selection = option_menu("Coil Selection", op_coil_outcm,
                                    default_index = 0, menu_icon="box-fill",
                                    styles=menu_style)
                
        #
    if shutdown:
        # Si, hay que eliminar las carpetas . De hecho hay que procesar todas
        # las entradas del st.session_state[mchnvec_ordr|mchn_plnt][platform] para 
        # ir borrando procesos y carpetas.
        kill_agents(log_mach,directory_log,1,1)
        #
        for mach in st.session_state['mchnvec_ordr'][platform]['dirs'].keys():
            if '--' not in mach:
                killall = "ssh "+str(mach)+' "killall python3"'
                out_1 = subprocess.Popen(killall, stdout=None, stdin=None, stderr=None, \
                                close_fds=True, shell=True, universal_newlines = True)
                killall = "ssh "+str(mach)+' " rm -rf ./tmp*"'
                out_2 = subprocess.Popen(killall, stdout=None, stdin=None, stderr=None, \
                                close_fds=True, shell=True, universal_newlines = True)
        for mach in st.session_state['mchnvec_plnt'][platform]['dirs'].keys():
            if '--' not in mach:            
                killall = "ssh "+str(mach)+' "killall python3"'
                out_1 = subprocess.Popen(killall, stdout=None, stdin=None, stderr=None, \
                                close_fds=True, shell=True, universal_newlines = True)
                killall = "ssh "+str(mach)+' " rm -rf ./tmp*"'
                out_2 = subprocess.Popen(killall, stdout=None, stdin=None, stderr=None, \
                                close_fds=True, shell=True, universal_newlines = True)
        # Terminar el proceso.
        st.stop()
        sys.exit()
#
if __name__ == "__main__":
    main()
