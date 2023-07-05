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
import signal
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
#Static page footer
addfooter = """
<style>
#MainMenu{
    visibility:hidden;
}
footer{
    visibility:visible;
}
footer:before{
    content: 'Developed by Joaquin Ordieres & Adriana Leria';
    display:block; position:relative; 
    }
</style>
"""
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
#cambios de colores, corregir checkbox
st.markdown(""" 
    <style>
        div.stButton > button:first-child {
            background-color: #ADD8E6;color:#ffffff;
            font-family: sans-serif;
        }
        div.stButton > button:hover {
            background-color: #000080;color:#ffffff; border-color:#050000;
            font-family: sans-serif;
        }
        div.stDownloadButton > button:first-child {
            background-color: #ADD8E6;color:#ffffff;
            font-family: sans-serif;
        }
        div.stDownloadButton > button:hover {
            background-color: #000080;color:#ffffff; border-color:#050000;
            font-family: sans-serif;
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
                font-family: sans-serif;            
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
    if 'plnt_selection' not in st.session_state:
        st.session_state['plnt_selection'] = 'Select a Plant'
    if 'ordr_selection' not in st.session_state:
        st.session_state['ordr_selection'] = 'Select an Order'
    if 'cl_selection' not in st.session_state:
        st.session_state['coil_selection'] = 'Select Coil'
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
        try: 
            lgf  = pd.read_csv(path,sep=';',header=None)
        except:
            return None
        lgf.columns = ['dtime','type','Agnt','Carrier','metadata']
        lgf['dtime'] = pd.to_datetime(lgf['dtime'])
        lgf  = lgf.loc[lgf['metadata'].str.len() > 2,:]
        lgf['dict']  = lgf['metadata'].apply(json.loads)
        idx  = lgf['dict'].apply(lambda x: 'Profit' in x[0].keys())
        try: 
            idxu = lgf.loc[idx].index[lgf['dict'].loc[idx].apply(len).astype(float).argmax()]
        except:
            return None
        rst  = pd.DataFrame(lgf['dict'].loc[idxu])
        return({'mainlog':lgf,'metadata':rst, 'idxres':idxu})
    else:
        return None
#
def find_vals(obj,key,txt):
    if key in obj.keys():
        if obj[key] is None:
            return(False)
        if txt in obj[key]:
            return True
    return False
#
def build_dct(lst):
    res = {}
    for i in lst:
        lst2 = i.split(':')
        clv = lst2[0].strip()
        val = ':'.join([k.strip() for k in lst2[1:]])
        if clv == 'code':
            val = re.sub(r"^c",'',val)
        res[clv] = val
    return(res)
#
def auctions_log(lgs,mdt):
    #
    # Processing END
    jdx  = lgs['dict'].apply(lambda x: find_vals(x[0],'location_2','END'))
    endt = lgs['dict'].loc[jdx].reset_index(drop=True)
    res0 = endt.apply(lambda x: {'agid':x[0]['coil_auction_winner'], \
            'Length':x[0]['coil_length'],'Width':x[0]['coil_width'],\
            'Thickness':x[0]['coil_thickness'],'Weight':x[0]['coil_weight'],\
            'ShipDate':x[0]['ship_date'],'ActiveCoils':x[0]['active_coils'],\
            'AuctionCoils':x[0]['auction_coils'][0].replace('"[','').replace(']"',''\
            ).replace('[','').replace(']','').replace(' ','').replace("'",""\
            ).split(',')})
    sbs0 = pd.DataFrame(res0.tolist())
    #
    # Processing ENDEDUP
    jdx  = lgs['dict'].apply(lambda x: find_vals(x[0],'msg','ENDEDUP'))
    endup= lgs['dict'].loc[jdx].reset_index(drop=True)
    res  = endup.apply(lambda x: x[0]['msg'].replace('ENDEDUP: ','id:'))
    sbs  = pd.DataFrame(res.apply(lambda x: build_dct(x.split(','))).tolist())
    #
    # Processing AU_ENDED
    jdx  = lgs['dict'].apply(lambda x: find_vals(x[0],'msg','AU_ENDED'))
    ended= lgs['dict'].loc[jdx].reset_index(drop=True)
    res2 = ended.apply(lambda x: x[0]['msg'].replace('AU_ENDED:','plant:'))
    sbs2 = pd.DataFrame(res2.apply(lambda x: build_dct(x.split(','))).tolist())   
    #
    # Preprocessing Auction Start End and Coils participating ...
    jdx  = lgs['dict'].apply(lambda x: find_vals(x[0],'msg','send pre-auction'))
    aunum= lgs['dict'].loc[jdx].apply(lambda x: x[0]['number']).astype(int).tolist()
    numc = lgs['dict'].loc[jdx].apply(lambda x: len(json.loads(x[0]['to']))).tolist()
    stxt = lgs.loc[jdx,'dtime'].tolist()
    jdx2 = lgs['dict'].apply(lambda x: find_vals(x[0],'msg','send acceptance'))
    etxt = lgs.loc[jdx2,'dtime'].tolist()
    sbs3 = pd.DataFrame({'AuctionID':aunum,'NumC':numc,'AuctionStart':stxt,
                         'AuctionEnd':etxt})
    #
    # merging components
    mg0  = pd.merge(mdt,sbs0,left_on="Coil",right_on="agid")
    mg0  = mg0.drop(['agid'], axis=1)
    mg1  = pd.merge(mg0,sbs,left_on="Coil",right_on="id")
    mg1  = mg1.drop(['id'], axis=1)
    mg2  = pd.merge(mg1,sbs2[['plant','auction','winner']],left_on="Coil", \
                    right_on="winner")
    mg2  = mg2.drop(['winner'], axis=1)
    mg2['auction'] = mg2['auction'].astype(int)
    mg3  = pd.merge(mg2,sbs3,left_on='auction',right_on='AuctionID')
    mg3  = mg3.drop(['AuctionID'],axis=1)
    mg3.index = mdt.index
    return(mg3)
#
#
#
#
def main():
    #
    # ==================================================================================================
    # Main program
    #
    st.markdown(addfooter, unsafe_allow_html=True)
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
    st.session_state['state'] = os.getpid()
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
    #left_gnrlsect.image('logo.png', width=128)
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
        left_gnrlsect.image('logo2.png', use_column_width = True)
        #left_gnrlsect.image('logo.png', width=128)
        left_gnrlsect.header('Welcome!')
        left_gnrlsect.write('Here you will manage your Multi-agent System.')
        left_gnrlsect.write('You will be able of keeping track of your agents and bids, their statuses and even uploading order forms and launching them!')
        center_gnrlsect.write('\n\n\n\n')
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
        st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudfare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" crossorigin="anonymous">', unsafe_allow_html=True)
        original_warning =  '<p style="font-family:sans-serif; color:Red; font-size: 20px;">' + \
                            '<i class="fa-light fa-triangle-exclamation"></i><b><it>Please, to start the session you need to pick the plant(s) ' + \
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
            #left_gnrlsect.image('logo.png', width=128)
            st.session_state['placeholder'] = placeholder
        #
    if platform != DEFAULT_pltfrm:
        #Static page header
        st.markdown('<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">', unsafe_allow_html=True)
        st.markdown("""
        <nav class="navbar fixed-top navbar-expand-lg navbar-dark" style="background-color: #000080; top: 5%;">
            <a class="navbar-brand" href="https://www.upm.es/observatorio/vi/index.jsp?pageac=actividad.jsp&id_actividad=311548" target="_blank" >DynReAct</a>
            <img src= "logo.png" style="widht:30px;height:20px"/>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item">
                        <a class="nav-link" href="https://www.upm.es/observatorio/vi/index.jsp?pageac=actividad.jsp&id_actividad=311548" target="_blank">About Us</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="mailto:a.leria@alumnos.upm.es">Contact Us</a>
                    </li>
                </ul>
            </div>
        </nav>    
        """, unsafe_allow_html=True)
        #
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
        left_gnrlsect.image('logo.png', width = 250)
        request_agent_list = right_gnrlsect.button('Agent List?')
        st.session_state['req_agnt_lst'] = request_agent_list
        #
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
        #
        if df_st.shape[0] > 0:
            st.session_state['df_st'] = df_st
        #
            #st.markdown("**_____________________________________________________________________**")            
        #
        #
        #
        vplntsel = False
        if 'current_tab' not in locals():
            old_tab  = ''
        else:
            old_tab  = current_tab
        #
        over_theme = {'txc_inactive': '#ffffff', 'menu_background': '#000080'}
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
            df_cnt = center_gnrlsect.container()
            df_container = df_cnt.empty()
            try:
                df_st = st.session_state['df_st']
            except:
                st.warning("Error: DF_ST not defined")
            df_container.dataframe(df_st)
        #
    #
    if current_tab == 'Home':
        # st.write(st.session_state['mchn_ordr'], 'Order')
        # st.write(st.session_state['mchn_plnt'], 'Plant')
        df_container = st.container()
        #
        df_container.header("Your Journey Starts Here")
        df_container.write('\n\n\n\n')
        df_container.markdown("""
            <div style="font-family: sans-serif; text-align: justify;">
                <h4>Welcome!</h4>
                <p>
                You've already accomplished the first step; you've selected the targeted Plant(s) and negotiation site for the simulation. 
                </p>
                <p>
                As you can see in the middle section of the page, you'll find a table displaying the number of Agents running at the momment. 
                To update these values, please click on <i>"Agent List?"</i> and the most up to date data will be displayed
                </p><p>
                Then, you should designate the Orders you want to launch. You'll find the list of Lots of orders planned for your targeted Plant(s) under 
                the tab <b>"Orders"</b>. Once the orders have been launched, on the right side of the page you'll be able to track the Order Codes that have been submitted.
                </p><p>  
                The next step is to select the Plant(s). You'll find the list of Plant(s) you've already selected in the landing page under the tab <b>"Plants"</b>. 
                As mentioned above, once the plant(s) have been launched, on the right side of the page you'll be able to track the Plant(s) that have been submitted.
                </p><p>
                Finally, after the scheduling is finished and all the bids have been completed (you can check this by seeing that the nº of Coils is 0). 
                You can check the results of the bids by going to the tab: <b>"Outcome</b>". Here, you'll be able to check the most important metrics for any of the agents (Plant, Order, Coil)
                and you'll be able to export the data to an excel file, by clicking on the <i>"Export"</i> button.
                </p><p>
                Once you've finished your tasks, please remember to click on <b>"Shutdown"</b>, and your session will be automatically terminated. Thank you!
                </p>
                <p>
                If you experience any issue or you have any feedback to give us, please do not hestitate to click on "Contact Us" in the top of the page, and let us know how we can support you.
                </p>
            </div>
        """, unsafe_allow_html=True)
        shutdown = df_container.button('Shutdown')
        st.session_state['shutdown'] = shutdown
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
        #try:
        #    df_st = st.session_state['df_st']
        #except:
        #    st.warning("Error: DF_ST not defined")
        #
        #df_container.dataframe(df_st)
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
        shutdown = st.button('Shutdown')
        st.session_state['shutdown'] = shutdown
        # pdb.set_trace()
    # 
    if current_tab == 'PLANTS':
        st.empty()
        left_plnt, centr_plnt, right_plnt = st.columns((1,2,1))
        df_cnt = centr_plnt.container()
        df_container = df_cnt.empty()
        # st.markdown("**_____________________________________________________________________**")
        #try:
        #    df_st = st.session_state['df_st']
        #except:
        #    st.warning("Error: DF_ST not defined")
        #
        #df_container.dataframe(df_st)
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
            if machine in st.session_state['mchnvec_plnt'][platform]['plnts']: 
                rgth1   = right_plnt.empty()
                rgth1.write('Plant(s) already submitted:')
                right_plnt.write(st.session_state['mchnvec_plnt'][platform]['plnts'][machine])
            #
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
        shutdown = st.button('Shutdown')
        st.session_state['shutdown'] = shutdown
    # Third part
    if current_tab == 'OUTCOME':
        st.empty()
        left_outcm, centrleft_outcm,right_outcm,last_outcm = st.columns((2,2,2,1))
        df_seleplnt_cnt= left_outcm.container()
        df_seleordr_cnt= centrleft_outcm.container()
        df_selecoil_cnt= right_outcm.container()
        df_seletable_cnt= last_outcm.container()
        df_cnt_1 = df_seleplnt_cnt.empty()
        df_cnt_2 = df_seleordr_cnt.empty()
        df_cnt_3 = df_selecoil_cnt.empty()
        df_cnt_4 = df_seletable_cnt.empty()
        #extraer TODAS las plantas activas
        plnt_list = []
        ordr_list = []
        # pdb.set_trace()
        for mach in st.session_state['mchnvec_plnt'][platform]['plnts'].keys():
            for i in st.session_state['mchnvec_plnt'][platform]['plnts'][mach]: 
                plnt_list.append(i)
        for mach in st.session_state['mchnvec_ordr'][platform]['ords'].keys():
            for j in st.session_state['mchnvec_ordr'][platform]['lnos'][mach]: 
                ordr_list.append(j['oname'])
        plnt_outcm_list = ['Select a Plant'] + list(set(plnt_list))
        ordr_outcm_list = ['Select an Order'] + list(set(ordr_list)) 
        # We check the last date for the log.log file
        if 'lastlog_date' in st.session_state:
            lastlog_date = st.session_state['lastlog_date']
            first_outcome= False
        else:
            lastlog_date = datetime.datetime.now()
            first_outcome= True
        elapsed = (datetime.datetime.now() - lastlog_date).total_seconds()
        if elapsed > 120 or first_outcome:
            tmpres = recovery_log(platform,True,True)
            if tmpres:
                st.session_state['lastlog_date']= datetime.datetime.now()
                first_outcome= False
        else: # Without remote copy of log.log
            tmpres = recovery_log(platform,True,False)
        if tmpres:
            loga = tmpres['mainlog']
            logb = tmpres['metadata']
            sbst = auctions_log(loga,logb)
            sbst.columns = ['Coil', 'Minimum Price', 'Bid', 'Difference', 'Remaining Budget', \
                        'Counterbid', 'Profit', 'ProdCost', 'TransportCost', 'EnergyCost', \
                        'initial_thickness', 'PlantRule', 'OilSorte', 'final_thickness', \
                        'Length', 'Width', 'Thickness', 'Weight', 'ShipDate', 'ListParticipants', \
                        'AuctionCoils', 'code', 'Order', 'by', 'offer', 'plant', 'AuctionID', \
                        'NumberParticipants','AuctionStart','AuctionEnd']
        # Proceed with menus
        st.session_state['title_df_export'] = 'empty.xlsx'
        st.session_state['df_export'] = pd.DataFrame()
        st.session_state['pointer'] = ''
        with df_cnt_1:
            plnt_selection = option_menu("Plant Selection", plnt_outcm_list,
                                default_index = 0, menu_icon="building",
                                styles=menu_style)
        if plnt_selection != st.session_state['plnt_selection']:
                st.session_state['plnt_selection'] = plnt_selection
        if st.session_state['plnt_selection'] == 'Select a Plant':
            st.session_state['ordr_selection'] = 'Select an Order'
            st.session_state['coil_selection'] = 'Select Coil'
            st.session_state['pointer'] = 'Plant'
        if st.session_state['plnt_selection'] != 'Select a Plant':
            st.session_state['title_df_export'] = 'plt'+ plnt_selection +'.xlsx'
            st.session_state['df_export'] = sbst.loc[:,['Order','Coil','Thickness','Width','Length',\
                                'Minimum Price', 'Bid', 'ProdCost', 'TransportCost',\
                                'EnergyCost','PlantRule','OilSorte','AuctionID']]
            st.session_state['pointer'] = 'Plant'
            st.write('----')
            with df_cnt_2:
                ordr_selection = option_menu("Order Selection", ordr_outcm_list,
                                    default_index = 0, menu_icon="envelope",
                                    styles=menu_style)
                if ordr_selection != st.session_state['ordr_selection']:
                    st.session_state['ordr_selection'] = ordr_selection
                if st.session_state['ordr_selection'] == 'Select an Order':
                    st.session_state['coil_selection'] = 'Select Coil'
                    st.session_state['pointer'] = 'Order'
                if st.session_state['ordr_selection'] != 'Select an Order':
                    st.session_state['title_df_export'] = 'ordr'+ ordr_selection +'.xlsx'
                    st.session_state['df_export'] = sbst.loc[sbst.Order==ordr_selection,['Coil','AuctionStart','AuctionEnd',\
                                'Minimum Price','Bid','Difference','Remaining Budget',\
                                'Counterbid', 'Profit','AuctionID']]
                    st.session_state['pointer'] = 'Order'
            with df_cnt_3: 
                op_coil_outcm = ['Select '+DEFAULT_outcm_coil] + \
                            st.session_state['mchnvec_ordr'][platform]['clts']
                coil_selection = option_menu("Coil Selection", op_coil_outcm,
                                    default_index = 0, menu_icon="box-fill",
                                    styles=menu_style)
                if coil_selection != 'Select Coil':
                    st.session_state['coil_selection'] = coil_selection
                if st.session_state['coil_selection'] != 'Select Coil':
                    st.session_state['title_df_export'] = 'cl'+ coil_selection +'.xlsx'
                    st.session_state['df_export'] = sbst.loc[sbst.code==coil_selection,['AuctionID','NumberParticipants','ListParticipants']]
                    st.session_state['pointer'] = 'Coil'
                #dowloand selection as xlsx
                if not(st.session_state['df_export'].empty): 
                    st.session_state['df_export'].to_excel(st.session_state['title_df_export'])
                    with open(st.session_state['title_df_export'], 'rb') as my_file:
                        df_cnt_4.download_button(label = 'Export', data = my_file, file_name = st.session_state['title_df_export'], \
                                            mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') 
        if not(st.session_state['df_export'].empty):
            if st.session_state['pointer'] == 'Plant':
                st.dataframe(st.session_state['df_export'], \
                        column_config={
                            "Minimum Price": st.column_config.NumberColumn(disabled = "True", format="$%d"),
                            "ProdCost": st.column_config.NumberColumn(disabled = "True", format="$%d"),
                            "TransportCost": st.column_config.NumberColumn(disabled = "True", format="$%d"),
                            "EnergyCost": st.column_config.NumberColumn(disabled = "True", format="$%d")
                        },use_container_width = True, hide_index=True)
            elif st.session_state['pointer'] == 'Order':
                st.dataframe(st.session_state['df_export'], \
                        column_config={
                            "Minimum Price": st.column_config.NumberColumn(disabled = "True", format="$%d"),
                            "Remaining Budget": st.column_config.NumberColumn(disabled = "True", format="$%d"),
                            "Profit": st.column_config.NumberColumn(disabled = "True", format="$%d")
                        }, use_container_width = True, hide_index=True)
            else:
                st.dataframe(st.session_state['df_export'], \
                        column_config={
                            "ListParticipants": st.column_config.ListColumn()
                        }, use_container_width = True, hide_index=True)
            st.write("*Search through data by clicking the table and using hotkeys (Ctrl + F) to bring up the search bar, and using the search bar to filter data.*")
        shutdown = st.button('Shutdown')
        st.session_state['shutdown'] = shutdown
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
        #st.markdown("""<meta http-equiv="refresh" content="0"></meta>""", unsafe_allow_html=True)
        os.kill(st.session_state['state'], signal.SIGKILL)
        st.write("Stopped process with pid:", st.session_state['state'])
        st.session_state['state'] = None
        st.stop()
        sys.exit()
        #
#
if __name__ == "__main__":
    main()
