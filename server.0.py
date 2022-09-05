from inspect import trace
import sys,os, subprocess, argparse
import time,datetime, ast, json
import tempfile, globals, pdb
#
import numpy as np 
import pandas as pd
import streamlit as st
#
from argparse import ArgumentParser
from ast import literal_eval
from streamlit_option_menu import option_menu
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

st.set_page_config(
  page_title='UX Industry Process Optimizer', 
  page_icon="random", 
  layout='centered', 
  initial_sidebar_state='auto', 
  menu_items={'Get Help':'https://github.com/marocas035/MARSS'}
  )

#st.markdown(html_string, unsafe_allow_html=True)
st.markdown("<style>.element-container{opacity:1 !important}</style>", unsafe_allow_html=True)

# Check if keys already exists in session_state --> si se está ejecutando el programa por primera vez, o por ejemplo me he ido a comer y he vuelto

if 'directory' not in st.session_state:
  st.session_state.directory = ''
if 'file' not in st.session_state:
  st.session_state.file = ''
if 'tab1' not in st.session_state:
  st.session_state.tab1 = ''
if 'tab2' not in st.session_state:
  st.session_state.tab2 = ''


DEFAULT = '--Pick a value--'

st.markdown(
    """
<style>
div[role="selectbox"] li:nth-of-type(1){
    background-color: blue;
}

</style>
""",
    unsafe_allow_html=True,
)

#st.markdown(""" 
#<style>
#div.stButton > button:first-child {
#background-color: #00cc00;color:white;font-size:20px;height:3em;width:30em;border-radius:10px 10px 10px 10px;
#}
#<style>
#""", unsafe_allow_html=True)

def selectbox_with_default(obj,text, values, default=DEFAULT, sidebar = False):
    func = obj.sidebar.selectbox if sidebar else obj.selectbox
    return func(text, np.insert(np.array(values,object),0,default))

@st.experimental_memo(suppress_st_warning=True)
def get_directory (log_mach):
    oshl = 'rsh '+str(log_mach)+' mktemp -d -p .'
    out  = subprocess.Popen(oshl, stdout=subprocess.PIPE, stdin=None, stderr=None, \
                        close_fds=True, shell=True, universal_newlines = True)
    my_dict, err_1 = out.communicate()
    return(my_dict.strip())

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
    brwst, err_2 = out_1.communicate()
    #
    return (int(logst),int(brwst))

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

def list_coils_orders_active(pltf,machine, log, browser, launcher, my_dict, password,loc=0):
    n_orders = 0
    n_coils  = 0
    lst_coils= pd.DataFrame()
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
        for j in globals.mchnvec[pltf]['dirs'].keys():
            rdir = globals.mchnvec[pltf]['dirs'][j]
            olcs = "ps -ax | grep coil.py | grep " + rdir + " | grep -v grep "
            out  = subprocess.Popen(olcs, stdout=subprocess.PIPE, stdin=None, \
                                stderr=subprocess.PIPE,close_fds=True, shell=True, \
                                universal_newlines = True)
            outlst, err = out.communicate()
            file_coils  = outlst.split('\n')
            # Pendiente de ver qué devuelve para porganizarlo
    return n_coils , n_orders , lst_coils


def list_plants_active(pltf,machine, log, browser, launcher, my_dict,password,loc=0):
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
        for j in globals.mchnvec[pltf]['dirs'].keys():
            rdir = globals.mchnvec[pltf]['dirs'][j]
            olcs = "ps -ax | grep python3 | grep " + rdir + " | grep -v log.py "
            olcs = "| grep -v coil.py | grep -v browser.py | grep -v grep "
            out  = subprocess.Popen(olcs, stdout=subprocess.PIPE, stdin=None, \
                                stderr=subprocess.PIPE,close_fds=True, shell=True, \
                                universal_newlines = True)
            outlst, err = out.communicate()
            file_coils  = outlst.split('\n')
            # Pendiente de ver qué se recupera para organizarlo
        n_plants = 0
    return n_plants, lst_plnts

@st.experimental_memo(suppress_st_warning=True)
def display_table(platform, log_mach, log, browser, launcher, directory, password):
    n_coils, n_orders, list_coils = list_coils_orders_active(platform,log_mach, log, \
                                        browser, launcher, directory, password,1)
    n_plants, list_plants = list_plants_active(platform,log_mach, log, browser, \
                                        launcher,directory, password,1)
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

def prepare_file (uploaded_file):
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

@st.experimental_memo
def launch_plant(plant_machine, directory_plant, platform, password):
  #file3 = list_bids(planta)
  chart_data = pd.DataFrame(
  np.random.randn(2, 3),
  columns = ['a', 'b', 'c'])
  st.dataframe(chart_data)
  return 


def execute_plant(plant_machine, directory_plant, platform, password):
    oshl = 'rsh '+str(plant_machine)+' "grep \'INFO;va;\' log.log | grep '"END"' | wc -l"'
        
    out = subprocess.Popen(oshl, stdout=subprocess.PIPE, stdin=None, stderr=None, \
                        close_fds=True, shell=True, universal_newlines = True)
    output, err = out.communicate()
    #list_bids(platform)
    return 

@st.experimental_memo(suppress_st_warning=True)
def convert_df(df):
    return df.to_csv()

def tabs(default_tabs = [], default_active_tab=0):
    #https://discuss.streamlit.io/t/multiple-tabs-in-streamlit/1100/21

    if not default_tabs:
        return None
    active_tab = st.radio("", default_tabs, index=default_active_tab, key='tabs')
    child = default_tabs.index(active_tab)+1
    st.markdown("""  
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
    return active_tab

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
parser.add_argument("--log_mach", help="Machine where the log.log file is going to be stored")

try:
    globals.directory_log = None
    globals.pltfrm = DEFAULT
    globals.pltvec = {}
    globals.mchn   = DEFAULT
    globals.mchnvec= {}
    globals.ordrs  = DEFAULT
    globals.ordsvec= {}
    lst_orders     = []
    pressLO        = False
    ordf           = DEFAULT
    uploaded_file  = None
    args           = argparse.Namespace()
    args           = parser.parse_args()
except SystemExit as e:
    # This exception will be raised if --help or invalid command line arguments
    # are used. Currently streamlit prevents the program from exiting normally
    # so we have to do a hard exit.
    os._exit(e.code)

machines_parser = args.machines
platforms_parser = args.platforms
log_mach = args.log_mach
password = 'DynReact'
#
df = pd.DataFrame({
  'apiict': platforms_parser})
df2 = pd.DataFrame({
  'machines': machines_parser})
yes_no = pd.DataFrame({
  'check': ['Yes', 'No']})
df3 = df2

col_0, col_1, col_2 = st.columns((2,4,1))
col_0.image('logo.png', width=64)
#Poner mensaje en cuadrado que se vea arriba
platform = selectbox_with_default(col_1,'Platform:', df['apiict'])
log      = 'log@' + str(platform)
browser  = 'browser@' + str(platform)
launcher = 'launcher@' + str(platform)    
#
if globals.pltfrm != platform: # We have changed the platform
    if platform in globals.mchnvec.keys() :
        directory_log = globals.mchnvec[platform]['pltd']
    else:
        directory_log = turn_on_systm(log_mach)
        globals.mchnvec[platform] = {}
        globals.mchnvec[platform]['srvn'] = log_mach # machine for log/browser
        globals.mchnvec[platform]['pltd'] = directory_log # directory for log/browser in log_mach       
        globals.mchnvec[platform]['ords'] = {} # list of files per machine
        globals.mchnvec[platform]['lnos'] = {} # list of order codes per machine
        globals.mchnvec[platform]['dirs'] = {} # directory per machine
        globals.mchnvec[platform]['clts'] = [] # directory per machine
    log_st, brw_st = check_agents(log_mach, platform, password, directory_log)
    globals.directory_log = directory_log
    #
    shutdown = col_2.button('Shutdown')    
    globals.pltfrm = platform
    Status   = 'Deactivated'
    n_coils  = '-'
    n_plants = '-'
    n_orders = '-'
    n_agents = '-'
    df_st = pd.DataFrame({
        'Selected platform': [platform],
        'Status': [Status],
        'Nº agents': [n_agents],
        'Nº plants': [n_plants],
        'Nº Orders': [n_orders],
        'Nº Coils': [n_coils] }).set_index('Selected platform')
    #
    if log_st != 1 or brw_st != 1:
        kill_agents(log_mach,directory_log,log_st,brw_st)
        initialize_agents(log_mach, platform, password, directory_log)
    else:
        res   = display_table(platform, log_mach, log, browser, launcher, \
                              directory_log, password)
        df_st = res['df'].set_index('Selected platform')
    # col_0.header("General Status")
    title_container= st.container()
    with title_container:
        col0, col1, col2, col3 = title_container.columns((1,1,1,1))
        st.dataframe(df_st)
        request_agent_list = col_2.button('Agent List?')
    #
    st.markdown("_______________________________________________________________")
    # st.header("Órdenes")
    #
    # Habría que ver si lo de abajo debería ser una función callback del botón 'on click'.
    if request_agent_list:
        res   = display_table(platform, log_mach, log, browser, launcher, \
                              directory_log, password)
        df_st = res['df'].set_index('Selected platform')
        title_container.empty()
        col0, col1, col2, col3 = title_container.columns((1,1,1,1))        
        title_container.dataframe(df_st)
        request_agent_list = False
    #
    # Seguramente el trabajo en cada región deberís encapsularse en una función y
    # usar las variables globales para mantener la lógica y el control ...
    with st.container():
        mid, col00, col01 = st.columns((1,2,1))
        machine = selectbox_with_default(mid,'Service Machine',df2['machines'])
        if globals.mchn == DEFAULT:
            placeholder1 = col00.empty()
            placeholder1.write('No Service Machine Selected')
        # We have changed the machine !!!
        if globals.mchn != machine: 
            if machine in globals.mchnvec[platform]['ords'].keys() :
                lst_orders = globals.mchnvec[platform]['ords'][machine]
            else:
                lst_orders = []
                globals.mchnvec[platform]['ords'][machine] = []
                globals.mchnvec[platform]['lnos'][machine] = []                
                globals.mchnvec[platform]['dirs'][machine] = ''
                globals.mchnvec[platform]['clts'].append(machine)
            globals.mchn = machine
        # Select orders when the machine has been setled up
        if globals.mchn != DEFAULT and ordf == DEFAULT: 
            placeholder1.empty()
            uploaded_file = col00.file_uploader("Load Orders File", type=['csv'])
        # track the orders and machines
        if uploaded_file != None:
            pdb.set_trace()
            ordf = uploaded_file.name
        if machine != DEFAULT and ordf != DEFAULT:
            if len(globals.mchnvec[platform]['dirs'][machine]) == 0:
                if machine != log_mach:
                    dir_orders= turn_on_systm(machine)
                    globals.mchnvec[platform]['dirs'][machine]=dir_orders
                else:
                    dir_orders= directory_log
                    globals.mchnvec[platform]['dirs'][machine]=dir_orders
            else:
                dir_orders= globals.mchnvec[platform]['dirs'][machine]
            # # Processing the orders file if not yet done
            if ordf not in globals.mchnvec[platform]['ords'][machine]:
                csv_file = pd.read_csv(uploaded_file,header=None, comment='#')
                csv_file = csv_file.iloc[:,0:7]
                placeholder02 = col01.empty()
                placeholder02.write('Order Loaded')
                detord   = prepare_file(csv_file)
                New_default = ''
                check = selectbox_with_default(col01,'Confirmation?', \
                                    yes_no['check'], New_default)
                if check == 'Yes':
                    pressLO = col01.button('Launch Order')
                if pressLO:
                    pressLO = False
                    col01.write('Order Launched')
                    #lanzar órdenes
                    launch_orders(detord,machine,dir_orders,platform,password)                    
                    globals.mchnvec[platform]['ords'][machine].append(ordf)
                    globals.mchnvec[platform]['lnos'][machine].append(detord['oname'])
                    ordf =  DEFAULT
                if check == 'No':
                    msg1 =  'Please, select again the machine or the order '
                    msg1 = msg1 + 'you would like to submit.'
                    col01.write(msg1)
        #
        # In another TAB 
        # Esto de abajo no lo he tocado ....
        if machine != DEFAULT:
            st.markdown("_______________________________________________________________")
            st.header("Plants Information")
            # grep 'INFO;va;' log.log | grep '"END"' | wc -l (END significa que hayan terminado una subasta; 
            # wc -l significa que le cuenta las lineas, cada linea seria una subasta)
            # so --> como ya sé los plantas que están activas, cuando entre abajo que desplegue el numero 
            # de tabs para cada planta activa
            # aqui da igual que se refresque porque cada vez que se activan nuevos puede que hayan entrado 
            # nuevas subastas o no
            # https://github.com/streamlit/release-demos/blob/0.84/0.84/demos/pagination.py para listas muy largas y poder ver distintas páginas

            # llamada a la función que muestre por pantalla los archivos de la planta 1
            # preguntar al launcher el resultado de las subastas en orden inverso al tiempo (sort)
            #
            with st.container():
                left, centr, right = st.columns((2,1,1))
                with left:
                    plant_machine = selectbox_with_default(left,'Plant Machine',df3['machines'])
                    placeholdernew = centr.empty()
                    placeholdernew.write('No Plant Machine Selected')
                #
                if plant_machine != DEFAULT:
                    directory_plant = turn_on_systm(plant_machine)
                    placeholdernew.write('Plant Machine Selected')
                    
                    #active_tab = tabs(so)
                    
                    tabss = [st.session_state.tab1, st.session_state.tab2]
                    active_tab = tabs(tabss)
                    if active_tab == st.session_state.tab1:
                        st.write("Welcome to the Plant Information Section")
                        boton = right.button('Refresh', key = 'refresh1')

                        plant_df = execute_plant(plant_machine, directory_plant, platform, password)
                        planta_df = pd.DataFrame(
                        np.random.randn(2, 3),
                        columns = ['a', 'b', 'c'])
                        st.dataframe(plant_df)
                        plant_csv = convert_df(plant_df)

                        st.download_button('Export', plant_csv, file_name = 'plantx_date_export',key = 'export1')
                        
                    elif active_tab == st.session_state.tab2:
                        st.write("Welcome to the Plant Information Section")
                        st.write("This is a secong tab example")
                        
                        boton2 = right.button('Refresh', key = 'refresh2')

                        plant_df2 = execute_plant(plant_machine, directory_plant, platform, password)
                        planta_df2 = pd.DataFrame(
                        np.random.randn(2, 3),
                        columns = ['a', 'b', 'c'])
                        st.dataframe(plant_df2)
                        plant_csv2 = convert_df(plant_df2)

                        st.download_button('Export', plant_csv2, file_name = 'plantx_date_export_2',key = 'export2')
                    else:
                        st.error("Something has gone terribly wrong.")
                
                    
                    st.write('Please, confirm you want to execute the plant in this machine:', machine)
                    New_default = ''
                    siplant = selectbox_with_default(
                        'Confirmation',
                        ['Yes', 'No'])

                    if siplant == 'Yes':
                        press_plant1 = right.button('Activate Plant')
                        if press_plant1:
                            placeholdernew.write('Plant Activated')
                            #lanzar órdenes
                            launch_plant(plant_machine, directory_plant, platform, password)
                            #qué pasa si le dan a este botón sin haber subido nada? poner algo para evitar este error

                    if siplant == 'No':
                        st.write('Please, select again the machine where you want to execute your order')
                
                else:
                    st.markdown("<i> This is the section where you will be able to see all the info related to the Active Plants  <br/> Please, select the Plant Machine </i>", unsafe_allow_html=True)

                

    # botón final de killall process y limpiar todo y botón de empezar todo? o ponerlo cada vez q seleccionas una plataforma?
    #m inuto 50 grabacion

    #---> REPENSAR
    if shutdown:
    #eliminar carpetas?
        for mach in machines_parser:
            killall = "rsh "+str(mach)+' "killall python3"'
            out = subprocess.Popen(killall, stdout=None, stdin=None, stderr=None, \
                                close_fds=True, shell=True, universal_newlines = True)
else:
    col_0.header('Welcome!')
    col_0.write('Here you will manage your Multi-agent System.')
    col_0.write('You will be able of keeping track of your agents and bids, their statuses and even uploading order forms and launching them!')
    col_0.warning('Please, to start the session you need to pick a value')
    col_1.image('logo2.png', use_column_width = True)