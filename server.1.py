from inspect import trace
import sys,os, subprocess, argparse
import time,datetime, ast, json
import tempfile, pdb
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
    page_icon="random",
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
@st.experimental_memo(suppress_st_warning=True)
def get_directory (log_mach):
    oshl = 'rsh '+str(log_mach)+' mktemp -d -p . '
    out  = subprocess.Popen(oshl, stdout=subprocess.PIPE, stdin=None, stderr=None, \
                        close_fds=True, shell=True, universal_newlines = True)
    my_dict, err_1 = out.communicate()
    return(my_dict.strip())
#
@st.experimental_memo(suppress_st_warning=True)
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
@st.experimental_memo(suppress_st_warning=True)
def initialize_agents(machine, platform, password, my_dict):
    log     = 'log@' + str(platform)
    browser = 'browser@' + str(platform)
    launcher= 'launcher@' + str(platform)
    fd,path = tempfile.mkstemp(prefix='tmp_',dir='/tmp/')
    fp = os.fdopen(fd,'w')
    fp.write("cd " + str(my_dict)+'\n')
    fp.write('/usr/bin/nohup /usr/bin/python3 ./log.py ' +\
             '-bag '+str(browser)+' -u '+str(log)+' -p '+password+' -w 900 &\n')
    fp.write('sleep 2\n')
    fp.write('/usr/bin/nohup /usr/bin/python3 ./browser.py ' +\
             ' -u '+str(browser)+' -p '+password+' -lag '+str(log)+ \
             ' -lhg '+str(launcher)+' -w 900 &\n')
    fp.close()
    oshl = " scp " + path + " @" + str(machine) +":" + my_dict + "/agorden.sh"
    err0 = subprocess.Popen(oshl, stdout=subprocess.PIPE, stdin=None, \
                        stderr=subprocess.PIPE, close_fds=True, shell=True)
    oshl1= 'rsh '+str(machine)+ ' "sh ' + str(my_dict) + '/agorden.sh"'
    time.sleep(2)
    err1 = subprocess.Popen(oshl1, stdout=subprocess.PIPE, stdin=None, \
                        stderr=subprocess.PIPE, close_fds=True, shell=True)
    os.remove(path)
    return(None)
#
@st.experimental_memo(suppress_st_warning=True)
def check_agents(machine, platform, password,my_dict):
    cmd  = " ps aux |grep python3 |grep log.py | wc -l"
    oshl = 'rsh '+str(machine) + cmd
    out_1= subprocess.Popen(oshl, stdout=subprocess.PIPE, stdin=None, stderr=None, \
                        close_fds=True, shell=True, universal_newlines = True)
    logst, err_1 = out_1.communicate()
    #
    cmd  = " ps aux |grep python3 |grep browser.py | wc -l"
    oshl = 'rsh '+str(machine) + cmd
    out_1= subprocess.Popen(oshl, stdout=subprocess.PIPE, stdin=None, stderr=None, \
                        close_fds=True, shell=True, universal_newlines = True)
    pdb.set_trace()
    brwst, err_2 = out_1.communicate()
    #
    return (int(logst),int(brwst))
#
@st.experimental_memo(suppress_st_warning=True)
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
@st.experimental_memo(suppress_st_warning=True)
def list_coils_orders_active(pltf, log, browser, launcher, my_dict, password,loc=0):
    n_orders = 0
    n_coils  = 0
    lst_coils= pd.DataFrame()
    pdb.set_trace()
    if loc==0:
        oshl = '/usr/bin/python3 ./agents/launcher.py '
        oshl = oshl+'--search aa=list -w 40 -bag '+str(browser)+' -lag '+str(log)
        oshl = oshl+' -u '+str(launcher)+' -p '+str(password)
        out  = subprocess.Popen(oshl, stdout=subprocess.PIPE, stdin=None, \
                                stderr=subprocess.PIPE,close_fds=True, shell=True, \
                                universal_newlines = True)
        outfile, err_2 = out.communicate()
        #Pendiente de ver que devuelve para organizarlo
        outfile = outfile.rstrip()
        print('list_coils',outfile)
        if outfile != '[]':
            file_coils= json.loads(outfile)
            lst_coils = pd.read_json(file_coils, orient='records')
            n_orders  = pd.unique(lst_coils['orden'])
            n_orders  = n_orders.shape
            n_orders  = int(''.join(map(str, n_orders))) 
            n_coils   = lst_coils.shape
            n_coils   = int(''.join(map(str, n_coils)))
            lst_coils = lst_coils['id']
    else:
        for j in st.session_state['mchnvec_ordr'][pltf]['dirs'].keys(): #recorre el nombre de las maquinas
            rdir = st.session_state['mchnvec_ordr'][pltf]['dirs'][j]
            olcs = "ps -ax | grep coil.py | grep " + rdir + " | grep -v grep "
            out  = subprocess.Popen(olcs, stdout=subprocess.PIPE, stdin=None, \
                                stderr=subprocess.PIPE,close_fds=True, shell=True, \
                                universal_newlines = True)
            outlst, err = out.communicate()
            lst_coils  = outlst.split('\n')
            # Pendiente de ver qué devuelve para porganizarlo
    return n_coils , n_orders , lst_coils
#
def list_plants_active(pltf, log, browser, launcher, my_dict,password,loc=0):
    lst_plnts= pd.DataFrame()
    n_plants = 0
    if loc == 0:
        oshl = '/usr/bin/python3 ./agents/launcher.py '
        oshl = oshl+'--search aa=aplist -w 40 -bag '+str(browser)+' -lag '+str(log)
        oshl = oshl+' -u '+str(launcher)+' -p '+str(password)
        out  = subprocess.Popen(oshl, stdout=subprocess.PIPE, stdin=None, \
                                stderr=subprocess.PIPE,close_fds=True, shell=True, \
                                universal_newlines = True)
        outfile, err_2 = out.communicate()
        # pendiente de ver que devielve para organizarlo
        outfile = outfile.rstrip()
    else:
        for j in st.session_state['mchnvec_ordr'][pltf]['dirs'].keys():
            rdir = st.session_state['mchnvec_ordr'][pltf]['dirs'][j]
            olcs = "ps -ax | grep python3 | grep " + rdir + " | grep -v log.py "
            olcs = olcs +  "| grep -v coil.py | grep -v browser.py | grep -v grep "
            out  = subprocess.Popen(olcs, stdout=subprocess.PIPE, stdin=None, \
                                stderr=subprocess.PIPE,close_fds=True, shell=True, \
                                universal_newlines = True)
            outlst, err = out.communicate()
            lst_plnts  = outlst.split('\n')
            # Pendiente de ver qué se recupera para organizarlo
        n_plants = 0
    return n_plants, lst_plnts
#
@st.experimental_memo(suppress_st_warning=True)
def display_table(platform, log_mach, log, browser, launcher, directory, password):
    pdb.set_trace()
    if platform == DEFAULT_pltfrm:
        dataframe = pd.DataFrame()
        list_plants = list_coils = []
    else:
        mthd = 1
        n_coils, n_orders, list_coils = list_coils_orders_active(platform, log, browser, \
                                            launcher, directory, password,mthd)
        n_plants, list_plants = list_plants_active(platform, log, browser, \
                                            launcher,directory, password,mthd)
        n_agents = n_coils + n_plants
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
@st.experimental_memo
def launch_orders (detorder, machine, my_dict, platform, password):
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
    oshl = " scp " + path + " @" + str(machine) +":" + my_dict + "/lchorden.sh"
    err0 = subprocess.Popen(oshl, stdout=subprocess.PIPE, stdin=None, \
                        stderr=subprocess.PIPE, close_fds=True, shell=True)
    oshl1= 'rsh '+str(machine)+ ' "sh ' + str(my_dict) + '/lchorden.sh"'
    time.sleep(2)
    err1 = subprocess.Popen(oshl1, stdout=subprocess.PIPE, stdin=None, \
                        stderr=subprocess.PIPE, close_fds=True, shell=True)
    os.remove(path)
    return(None)
#
@st.experimental_memo
def launch_plant(plant, machine, my_dict, platform, log, browser, password):
    plant = plant.lower()
    va = str(plant)+'@' + str(platform)
    #
    fd,path = tempfile.mkstemp(prefix='tmp_',dir='/tmp/')
    fp = os.fdopen(fd,'w')
    fp.write("cd " + str(my_dict)+ "\n")
    fp.write("/usr/bin/nohup /usr/bin/python3 " + str(my_dict)+ "/va.py ")
    fp.write("-an '"+str(plant[-1])+"' -sd '"+str(0.25))
    fp.write("' -bag " + str(browser) + " -lag " + str(log) + " -u ")
    fp.write(str(va)+" -p "+password+" &\n")
    fp.close()
    oshl = " scp " + path + " @" + str(machine) +":" + my_dict + "/lchorden.sh"
    err0 = subprocess.Popen(oshl, stdout=subprocess.PIPE, stdin=None, \
                        stderr=subprocess.PIPE, close_fds=True, shell=True)
    oshl1= 'rsh '+str(machine)+ ' "sh ' + str(my_dict) + '/lchorden.sh"'
    time.sleep(1)
    err1 = subprocess.Popen(oshl1, stdout=subprocess.PIPE, stdin=None, \
                        stderr=subprocess.PIPE, close_fds=True, shell=True)
    os.remove(path)
    time.sleep(3)
    if plant not in st.session_state['mchnvec_plnt'][platform]['plnts'][machine]:
        st.session_state['mchnvec_plnt'][platform]['plnts'][machine].append(plant)
    return(None)
#
def execute_plant(plant_machine, directory_plant, platform, password):
    oshl = 'rsh '+str(plant_machine)+' "grep \'INFO;va;\' log.log | grep '"END"' | wc -l"'
        
    out = subprocess.Popen(oshl, stdout=subprocess.PIPE, stdin=None, stderr=None, \
                        close_fds=True, shell=True, universal_newlines = True)
    output, err = out.communicate()
    #list_bids(platform)
    return 
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
        st.session_state['pltfrm']       = DEFAULT_pltfrm
        if platform == DEFAULT_pltfrm:
            lft.header('Welcome!')
            lft.write('Here you will manage your Multi-agent System.')
            lft.write('You will be able of keeping track of your agents and bids, their statuses and even uploading order forms and launching them!')
            st.warning('Please, to start the session you need to pick a value')
            cnt.image('logo2.png', use_column_width = True)
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
    if platform in st.session_state['mchnvec_ordr'].keys() :
        directory_log = st.session_state['mchnvec_ordr'][platform]['pltd']
    else:
        directory_log = turn_on_systm(log_mach)
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
    st.session_state['directory_log'] = directory_log
    st.session_state['pltfrm'] = platform
    res   = display_table(platform, log_mach, log, browser, launcher, \
                        directory_log, password)
    df_st = res['df']
    if df_st.shape[0] > 0:
        df_st.set_index('Selected platform',inplace=True) 
    return(directory_log, df_st)
#
def setup_order(platform,machine):
    if machine in st.session_state['mchnvec_ordr'][platform]['ords'].keys() :
        lst_orders = st.session_state['mchnvec_ordr'][platform]['ords'][machine]
    else:
        lst_orders = []
        st.session_state['mchnvec_ordr'][platform]['ords'][machine] = []
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
        st.session_state['mchnvec_plnt'][platform]['plnts'][machine] = []                
        st.session_state['mchnvec_plnt'][platform]['dirs'][machine] = ''
        st.session_state['mchnvec_plnt'][platform]['clts'].append(machine)
    st.session_state['mchn_plnt'] = machine
    return(lst_plnts)
#
def update_order(platform,machine,log_mach,ordf,uploaded_file):
    detord = {}
    if platform in st.session_state['mchnvec_ordr']:
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
    if ordf != DEFAULT:
        if ordf not in st.session_state['mchnvec_ordr'][platform]['ords'][machine]:
            csv_file = pd.read_csv(uploaded_file,header=None, comment='#')
            csv_file = csv_file.iloc[:,0:7]
            detord   = prepare_file(csv_file)
    return(detord)
#
def update_plant(platform,machine,log_mach,plnt):
    detord = {}
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
    return(dir_plnts)
#
def order_process(platform,machine,detord,ordf,password):
    #lanzar órdenes
    dir_orders = st.session_state['mchnvec_ordr'][platform]['dirs'][machine]
    launch_orders(detord,machine,dir_orders,platform,password)                    
    st.session_state['mchnvec_ordr'][platform]['ords'][machine].append(ordf)
    st.session_state['mchnvec_ordr'][platform]['lnos'][machine].append(detord['oname'])
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
    main_tabs = ['ORDERS','PLANTS']
    st.empty()
    title_container = st.container()
    #
    left_gnrlsect, center_gnrlsect, right_gnrlsect = title_container.columns((2,4,1))
    left_gnrlsect.image('logo.png', width=64)
    #
    platform = selectbox_with_default(center_gnrlsect, df['apiict'], DEFAULT_pltfrm)
    log      = 'log@' + str(platform)
    browser  = 'browser@' + str(platform)
    launcher = 'launcher@' + str(platform) 
    lst_orders     = []
    lst_plnts      = []
    pressLO        = False
    press_plant1   = False
    ordf           = DEFAULT  # Order file picked-up
    plntsel        = DEFAULT  # plants selected
    uploaded_file  = None
    init_vars(left_gnrlsect, center_gnrlsect,platform)
    #
    directory_log, df_st = setup(platform,log_mach,log,browser,launcher,password)         
    log_st, brw_st = check_agents(log_mach, platform, password, directory_log)
    shutdown = right_gnrlsect.button('Shutdown')
    #
    request_agent_list = right_gnrlsect.button('Agent List?')
    if log_st != 1 or brw_st != 1:
        kill_agents(log_mach,directory_log,log_st,brw_st)
        initialize_agents(log_mach, platform, password, directory_log)
    elif request_agent_list:
        directory_log, df_st = setup(platform,log_mach,log,browser,launcher,password)         
        request_agent_list = False                
    #
    if df_st.shape[0] > 0:
        title_container.dataframe(df_st)
    st.session_state['pltfrm'] = platform
    #
    if platform != DEFAULT_pltfrm:
        st.markdown("**_____________________________________________________________________**")
        # 
        # Orders panel (inside the platform)
        current_tab = tabs(st,main_tabs)
    else:
        current_tab = ''
    #
    if current_tab == 'ORDERS':
        #
        # Seguramente el trabajo en cada región debería encapsularse en una función y
        # usar las variables globales para mantener la lógica y el control ...
        st.empty()
        left_ordr, center_ordr, right_ordr = st.columns((1,2,1))
        machine  = selectbox_with_default(left_ordr,df2['machines'], DEFAULT_ordrs)
        cnt1 = center_ordr.empty()        
        if st.session_state['mchn_ordr'] == DEFAULT_ordrs:
            cnt11 = cnt1.write('No Service Machine Selected')
        if st.session_state['mchn_ordr'] != machine: # Change of Machine
            lst_orders = setup_order(platform,machine)
        # Select orders when the machine has been setled up
        if st.session_state['mchn_ordr'] != DEFAULT_ordrs and ordf == DEFAULT: 
            cnt1 = cnt1.empty()
            uploaded_file = cnt1.file_uploader("Load Orders File", type=['csv'])
        if uploaded_file != None:
            ordf = uploaded_file.name
        ext_ordrs= []
        if platform in st.session_state['mchnvec_ordr']:
            if machine in st.session_state['mchnvec_ordr'][platform]['ords']:
                ext_ordrs= st.session_state['mchnvec_ordr'][platform]['ords'][machine]
        if machine  != DEFAULT_ordrs and ordf not in ext_ordrs:
            detord  =  update_order(platform,machine,log_mach,ordf,uploaded_file)
            rgth1   =  right_ordr.empty()
            if len(detord) > 0:
                rgth11 = rgth1.write('Order Loaded')
                pressLO = rgth1.button('Launch Order')
                if pressLO:
                    rgth11 = rgth1.empty()                        
                    order_process(platform,machine,detord,ordf,password)
                    pressLO = False
                    right_ordr.write('Order Launched')
                    pdb.set_trace()
                    directory_log, df_st = setup(platform,log_mach,log,browser,\
                                                launcher,password)
                    ordf =  DEFAULT
    #
    # Segunda parte
    if current_tab == 'PLANTS':
        st.empty()
        left_plnt, centr_plnt, right_plnt = st.columns((1,2,1))
        plant_mchn = selectbox_with_default(left_plnt,df3['machines'],DEFAULT_mchn)
        cnt_plnt   = centr_plnt.empty()
        if st.session_state['mchn_plnt'] == DEFAULT_mchn:
            cnt_plnt.write('No Plant Machine Selected')
        # We have changed the server !!!
        if st.session_state['mchn_plnt'] != plant_mchn:
            lst_plnts = setup_plant(platform,plant_mchn)
        #
        if st.session_state['mchn_plnt'] != DEFAULT_mchn and plntsel == DEFAULT_plnts: 
            cnt_plnt.empty()
            plntsel   = cnt_plnt.selectbox(DEFAULT_plnts, \
                                        ('','VA08','VA09','VA10','VA11','VA12'))
        if plant_mchn != DEFAULT_mchn and plntsel not in lst_plnts:
            dir_plnts =  update_plant(platform,plant_mchn,log_mach,plntsel)
            rgtha     =  right_plnt.empty()
            rgtha.write('Plant Selected')
            press_plant1 = rgtha.button('Activate Plant')
            if press_plant1:
                launch_plant(plntsel,plant_mchn,dir_plnts,platform,password)
                press_plant1 = False
                plntsel  = DEFAULT_plnts  
        if plant_mchn != DEFAULT_mchn and plntsel != DEFAULT_plnts: 
            plants_tabs = st.session_state['mchnvec_plnt'][platform]['plnts']
            active_tab = tabs(left_plnt, plants_tabs)
            st.write("Welcome to the Plant " + active_tab + ". Information Section")
            boton = right_plnt.button('Refresh', key = 'refresh1')
            plant_df = execute_plant(plntsel,active_tab,plant_mchn,dir_plnts,\
                                        platform,password)
            centr_plnt.dataframe(plant_df)
        #
        #---> REPENSAR
    if shutdown:
        #eliminar carpetas?
        # Si, hay que eliminar las carpetas . De hecho hay que procesar todas
        # las entradas del st.session_state[mchnvec_ordr|mchn_plnt][platform] para 
        # ir borrando procesos y carpetas.
        for mach in machines_parser:
            killall = "rsh "+str(mach)+' "killall python3"'
            out = subprocess.Popen(killall, stdout=None, stdin=None, stderr=None, \
                                close_fds=True, shell=True, universal_newlines = True)
#
if __name__ == "__main__":
    main()