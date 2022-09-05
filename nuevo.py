import sys
import os, subprocess
import streamlit as st
import numpy as np 
import pandas as pd 
import time
import ast
import tempfile
import json


#En este script en vez de tener la posibilidad de elegir cualquier máquina para ejecutar el log y el browser, en esta primera sección del General Status
#Se establece una única máquina, para poder simplificar el proceso y mejorar la experiencia del usuario, ya que el usuario se preocupa únicamente desde dónde.
#se ha lanzado las órdenes, los agentes bobina y los agentes planta. 
#En un principio se ha elegido pasar el argumento por pantalla con la ayuda de la función argparse. Pero no se descarta la opción de que el usuario también pueda elegir la máuina para ejecutar el log 
#también al comienzo, cuando elige la plataforma donde se va a desarrollar todo el programa. Aunque se considera que esta forma no queda igual de bien visualmente para la experiencia del usuario.  

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

def selectbox_with_default(text, values, default=DEFAULT, sidebar = False):
  func = st.sidebar.selectbox if sidebar else st.selectbox
  return func(text, np.insert(np.array(values,object),0,default))

@st.experimental_memo(suppress_st_warning=True)
def tempofile(log_mach):

    #temp = tempfile.TemporaryFile()
    with tempfile.TemporaryDirectory() as temp:
      
      temp_file = temp.split('/')
      temp_file = temp_file[2]
      oshl_1 = 'rsh '+str(log_mach)+' "mkdir '+temp_file+'"'
      subprocess.Popen(oshl_1, stdout=None, stdin=None, stderr=None, \
                      close_fds=True, shell=True) 
    return temp_file

@st.experimental_memo(suppress_st_warning=True)
def get_directory (log_mach):
    
    oshl = 'rsh '+str(log_mach)+' "pwd"'

    out = subprocess.Popen(oshl, stdout=subprocess.PIPE, stdin=None, stderr=None, \
                        close_fds=True, shell=True, universal_newlines = True)
    my_dict, err_1 = out.communicate()

    temp_file = tempofile(log_mach)
    my_dict = my_dict.rstrip()
    directory = my_dict+'/'+temp_file
    return directory

@st.experimental_memo(suppress_st_warning=True)
def turn_on_log(log_mach):

    #crear my_dir  
    #primero tengo que copiar los files de los agents y luego puedo ejecutarlos
    #Para que se ejecute en otra máquina hay que poner delante la máquina remota que lo va a ejecutar

    my_dict = get_directory(log_mach)
    oshl_1 = "cd agents; scp *.py aleria@"+str(log_mach)+":"+my_dict

    subprocess.Popen(oshl_1, stdout=None, stdin=None, stderr=None, \
                        close_fds=True, shell=True)
    
    return my_dict

@st.experimental_memo(suppress_st_warning=True)
def turn_on_order(log_mach):

    #crear my_dir  
    #primero tengo que copiar los files de los agents y luego puedo ejecutarlos
    #Para que se ejecute en otra máquina hay que poner delante la máquina remota que lo va a ejecutar

    my_dict = get_directory(log_mach)
    oshl_1 = "cd agents; scp *.py aleria@"+str(log_mach)+":"+my_dict

    subprocess.Popen(oshl_1, stdout=None, stdin=None, stderr=None, \
                        close_fds=True, shell=True)
    
    return my_dict

@st.experimental_memo(suppress_st_warning=True)
def turn_on_plant(log_mach):

    #crear my_dir  
    #primero tengo que copiar los files de los agents y luego puedo ejecutarlos
    #Para que se ejecute en otra máquina hay que poner delante la máquina remota que lo va a ejecutar

    my_dict = get_directory(log_mach)
    oshl_1 = "cd agents; scp *.py aleria@"+str(log_mach)+":"+my_dict

    subprocess.Popen(oshl_1, stdout=None, stdin=None, stderr=None, \
                        close_fds=True, shell=True)
    
    return my_dict



@st.experimental_memo(suppress_st_warning=True)
def initialize_agents(machine, platform, password, my_dict):


    log = 'log@' + str(platform)
    browser = 'browser@' + str(platform)
    launcher = 'launcher@' + str(platform)

    oshl = 'rsh '+str(machine)+' "/usr/bin/nohup /usr/bin/python3 '+str(my_dict)+'/log.py'
    oshl = oshl+' -bag '+str(browser)+' -u '+str(log)+' -p '+password+' -w 900 &"'
    subprocess.Popen(oshl, stdout=None, stdin=None, stderr=None, \
                        close_fds=True, shell=True)
    oshl1 = 'rsh '+str(machine)+' "/usr/bin/nohup /usr/bin/python3 '+str(my_dict)+'/browser.py'
    oshl1 = oshl+' -u '+str(browser)+' -p '+password+' -lag '+str(log)+' -lhg '+str(launcher)+' -w 900 &"'
    subprocess.Popen(oshl1, stdout=None, stdin=None, stderr=None, \
                        close_fds=True, shell=True)
    print('a ver', oshl)
    return

@st.experimental_memo(suppress_st_warning=True)
def check_agents(machine, platform, password,my_dict):    
    oshl = 'rsh '+str(machine)+' "ps aux |grep python3 |grep aleria |wc -l"'
    out_1 = subprocess.Popen(oshl, stdout=subprocess.PIPE, stdin=None, stderr=None, \
                        close_fds=True, shell=True, universal_newlines = True)
    Status_c, err_1 = out_1.communicate()

    if int(Status_c) > 0:
      Status = "Activated"

      #oshl1 = 'rsh '+str(machine)+' "cd '+my_dict+'; grep \'DEBUG;browser;\' log.log |wc -l"'
      oshl1 = 'rsh '+str(machine)+' "grep \'DEBUG;browser;\' log.log |wc -l"'
      
      out_2 = subprocess.Popen(oshl1, stdout=subprocess.PIPE, stdin=None, stderr=None, \
                          close_fds=True, shell=True, universal_newlines = True)
      browser_active, err_2 = out_2.communicate()

      if int(browser_active) == 0:
        initialize_agents(machine, platform, password, my_dict)
        
    else:
        Status = "Deactivated"

    return browser_active, Status


def list_coils_orders_active(machine, log, browser, launcher, my_dict, password):

    oshl = "rsh "+str(machine)
    oshl = oshl+' "/usr/bin/nohup /usr/bin/python3 '+str(my_dict)+'/launcher.py'
    oshl = oshl+' --search aa=list -w 40 -bag '+str(browser)+' -lag '+str(log)+' -u '+str(launcher)+' -p '+str(password)+' & "'

    out = subprocess.Popen(oshl, stdout=subprocess.PIPE, stdin=None, stderr=None, \
                        close_fds=True, shell=True, universal_newlines = True)
    outfile, err_2 = out.communicate()
    outfile = outfile.rstrip()
    print('list_coils',outfile)
    list_coils = pd.DataFrame()
    if outfile != '[]':
      print("list is not empty", outfile)
      file_coils = json.loads(outfile)
      list_coils = pd.read_json(file_coils, orient='records')
      print('list_coils ',list_coils)
      n_orders = pd.unique(list_coils['orden'])
      n_orders = n_orders.shape
      n_orders = int(''.join(map(str, n_orders))) 
      n_coils = list_coils.shape
      n_coils = int(''.join(map(str, n_coils)))
      list_coils = list_coils['id']


    n_orders = 0
    n_coils = 0
    return n_coils , n_orders , list_coils


def list_plants_active(machine, log, browser, launcher, my_dict,password):

    oshl = "rsh "+str(machine)
    oshl = oshl+' "/usr/bin/nohup /usr/bin/python3 '+str(my_dict)+'/launcher.py'
    oshl = oshl+' --search aa=aplist -w 40 -bag '+str(browser)+' -lag '+str(log)+' -u '+str(launcher)+' -p '+str(password)+' & "'
    print('list_plants antes')
    out = subprocess.Popen(oshl, stdout=subprocess.PIPE, stdin=None, stderr=None, \
                        close_fds=True, shell=True, universal_newlines = True)
    outfile, err_2 = out.communicate()
    outfile = outfile.rstrip()
    print('list plants despues', outfile)
    list_plants = pd.DataFrame()
  
    #if outfile != '[]':
      #file_plants = json.loads(outfile)
      #list_plants = pd.read_json(file_plants, orient='records')
      #st.write('list_plants ',list_plants)
      #n_plants = list_plants.shape
      #n_plants = int(''.join(map(str, n_plants))) 
      #chequear si lista está empty --> todo = 0
    n_plants = 0
    return n_plants, list_plants


def list_bids(platform):
    
  return file

@st.experimental_memo(suppress_st_warning=True)
def display_table(Status, platform, log_mach, log, browser, launcher, directory, password, request_agent_list):

    if Status == "Activated":
        n_coils, n_orders, list_coils = list_coils_orders_active(log_mach, log, browser, launcher, directory, password)
        n_plants, list_plants = list_plants_active(log_mach, log, browser, launcher, directory, password)
        n_agents = n_coils + n_plants
    else:
        n_coils = '-'
        n_plants = '-'
        n_orders = '-'
        n_agents = '-'

    dataframe = pd.DataFrame({
    'Selected platform': [platform],
    'Status': [Status],
    'Nº agents': [n_agents],
    'Nº plants': [n_plants],
    'Nº Orders': [n_orders],
    'Nº Coils': [n_coils]
    })
    
    return dataframe


def prepare_file (uploaded_file):
  #leer y sacar los parámetros para hacer la ejecución

  so = []
  lp = []
  lc = []
  for row in uploaded_file.index:
    for indix, col in enumerate(uploaded_file):
        if row <= 5:
            if row == 0:
                if indix == 0:
                    oc = uploaded_file[col].values[row]
                elif indix == 1:
                    sg = uploaded_file[col].values[row]
                elif indix == 2:
                    at = uploaded_file[col].values[row]
                elif indix == 3:
                    uploaded_file[col].values[row].astype(int)
                    wi = uploaded_file[col].values[row]
                elif indix == 4:
                    uploaded_file[col].values[row].astype(int)
                    po = uploaded_file[col].values[row]
            elif row == 2:
                if pd.isnull(uploaded_file[col].values[row]):
                    pass
                else:  so.append(uploaded_file[col].values[row])
            elif row == 4:
                r = uploaded_file["# Order-name     Mat     Thickness    Width      Budget"].values[row]
            else:
                pass
    
        else:
            if indix == 0:
                lc.append(uploaded_file[col].values[row])
            elif indix == 1:
                lp.append(uploaded_file[col].values[row])

    return oc, sg, at, wi, po, so, lp, lc, r 


@st.experimental_memo
def launch_orders (oc, sg, at, wi, po, so, lp, lc, i, machine, my_dict, platform, password):
    
    log = 'log@' + str(platform)
    browser = 'browser@' + str(platform)
    launcher = 'launcher@' + str(platform)
    n = 0 
    #nohup /usr/bin/python3 /home/jb/agents_jb03/launcher.py -oc "O202109-01" -sg "X400" -at 0.3 -wi 985 -nc 4 -lc "cO202109101, cO202109102, cO202109103,cO202109104" -po 2000 -lp "NWW1,NWW1,NWW1,NWW1" -ll "20000,21000,19500,21500" -sd "2021-11-10" -so "VA0[8-9]" -w 40 
    #-bag browser@apiict00.etsii.upm.es -lag log@apiict00.etsii.upm.es -u launcher@apiict00.etsii.upm.es -p DynReact &
    oshl = 'rsh '+str(machine)+' "/usr/bin/nohup /usr/bin/python3 '+str(my_dict)+'/launcher.py'
    oshl = oshl+' -oc \"'+str(oc)+'\" -sg \"'+str(sg)+'\" -at '+str(at)+' -wi '+str(wi)+' -nc '+str(i)+' -lc \"'
    for x in lc:
        n += 1
        if n != len(lc):
            oshl = oshl+ str(x)+','
        else:
            oshl = oshl+ str(x)

    oshl = oshl+'\" -po '+str(po)+' -lp \"'
    n=0
    for y in lp:
        n += 1
        if n != len(lp):
            oshl = oshl+ str(y)+', '
        else:
            oshl = oshl+ str(y)
            
    oshl = oshl+'\" -so \"'
    for z in so:
        n += 1
        if n != len(so):
            st.session_state.tab1 = z
            oshl = oshl+ str(z)+', '
        else:
            oshl = oshl+ str(z)
            st.session_state.tab2 = z
    print('launch_orders', oshl)
    oshl = oshl+'\" -bag '+str(browser)+' -lag '+str(log)+' -u '+str(launcher)+' -p '+password+' -w 40 & "'
    subprocess.Popen(oshl, stdout=None, stdin=None, stderr=None, \
                        close_fds=True, shell=True)
    print('launch_orders', oshl)

    return 

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


import argparse 
parser = argparse.ArgumentParser()
#streamlit run nuevo.py -- --machines 138.100.82.175 --machines 138.100.82.241 --platforms apiict00.etsii.upm.es --platforms apiict01.etsii.upm.es
parser.add_argument("--machines", action='append', default=[],  help="Máquina operativa donde poder ejecutar los agentes")
parser.add_argument("--platforms", action='append', default=[],  help="Negotiating platforms for use")
parser.add_argument("--log_mach", help="Machine where the log.log file is going to be stored")


try:
    args = parser.parse_args()
except SystemExit as e:
    # This exception will be raised if --help or invalid command line arguments
    # are used. Currently streamlit prevents the program from exiting normally
    # so we have to do a hard exit.
    os._exit(e.code)

machines_parser = args.machines
platforms_parser = args.platforms
log_mach = args.log_mach
password = 'DynReact'


df = pd.DataFrame({
  'apiict': platforms_parser})
df2 = pd.DataFrame({
  'machines': machines_parser})
yes_no = pd.DataFrame({
  'check': ['Yes', 'No']})
df3 = df2

col_0, col_1 = st.columns((3,1))

#Poner mensaje en cuadrado que se vea arriba
platform = selectbox_with_default('Select the platform where you want to work.', df['apiict'])


if platform == DEFAULT:
    col_0.header('Welcome!')
    col_0.write('Here you will manage your Multi-agent System.')
    col_0.write('You will be able of keeping track of your agents and bids, their statuses and even uploading order forms and launching them!')
    col_0.warning('Please, to start the session you need to pick a value')
    col_1.image('logo.png', use_column_width = True)
else: 

    col_0.header("General Status")
    shutdown = col_1.button('Shutdown')
    

    title_container = st.container()
    with title_container:
        col0, col1, col2, col3 = title_container.columns((1,1,1,1))
        col0.image('logo.png', use_column_width = True)

        log = 'log@' + str(platform)
        browser = 'browser@' + str(platform)
        launcher = 'launcher@' + str(platform)

        #Problema con los directorios, si quiero evitar estar escribiendo y creando carpetas, necesito guardar de alguna manera [log, maquina, temporaryfile]
        #porque si no parece que se están sobreescribiendo

        directory_log = turn_on_log(log_mach)
        browser_active, Status = check_agents(log_mach, platform, password, directory_log)

        
        if int(browser_active) == 0:

            Status = 'Deactivated'
            n_coils = '-'
            n_plants = '-'
            n_orders = '-'
            n_agents = '-'

            dataframe_deactivated = pd.DataFrame({
            'Selected platform': [platform],
            'Status': [Status],
            'Nº agents': [n_agents],
            'Nº plants': [n_plants],
            'Nº Orders': [n_orders],
            'Nº Coils': [n_coils]
            })
            st.dataframe(dataframe_deactivated)

        #REVISAR --> tarda muchísimo
        request_agent_list = col2.button('Request Active Agent List')
        if int(browser_active) != 0 or request_agent_list:
            dataframe_stable = display_table(Status, platform, log_mach, log, browser, launcher, directory_log, password, request_agent_list)
            st.dataframe(dataframe_stable)


    st.markdown("_______________________________________________________________")
    st.header("Órdenes")


    #cuando yo lanzo el order file, estoy activando nuevos agentes por lo que si se consigue refrescar automáticamente la parte de arriba sería la leche y si no pues que la gente le de al botón de request active agent list


    with st.container():
        mid, col00, col01 = st.columns((1,1,1))
        with mid:
            machine = selectbox_with_default(
                'Service Machine',
                df2['machines'])
        placeholder1 = col00.empty()
        placeholder2 = col01.empty()
        placeholder1.write('No Service Machine Selected')
        placeholder2.write('No Order')
        
        #press1 = col00.button('Load Order File')    
        #if press1:

        uploaded_file = st.file_uploader("Load Order File", type=['csv'])
        if machine != DEFAULT:
            directory_order = turn_on_order(machine)
            placeholder1.write('Service Machine Selected')
            if uploaded_file is not None:
                
                csv_file = pd.read_csv(uploaded_file)
                placeholder2.write('Order Prepared')
                oc, sg, at, wi, po, so, lp, lc, i = prepare_file(csv_file)

                st.write('Please, confirm you want to execute your orders in this machine:', machine)
                New_default = ''
                check = selectbox_with_default(
                    'Confirmation?',
                    yes_no['check'], New_default)

                if check == 'Yes':
                    press2 = col01.button('Launch Order')
                    if press2:
                        placeholder2.write('Order Lunched')
                        #lanzar órdenes
                        launch_orders(oc, sg, at, wi, po, so, lp, lc, i,machine, directory_order, platform, password)

                if check == 'No':
                    st.write('Please, select again the machine where you want to execute your order')

    st.markdown("_______________________________________________________________")
    st.header("Plants Information")

    #grep 'INFO;va;' log.log | grep '"END"' | wc -l (END significa que hayan terminado una subasta; wc -l significa que le cuenta las lineas, cada linea seria una subasta)

    #so --> como ya sé los plantas que están activas, cuando entre abajo que desplegue el numero de tabs para cada planta activa
    #aqui da igual que se refresque porque cada vez que se activan nuevos puede que hayan entrado nuevas subastas o no
    #https://github.com/streamlit/release-demos/blob/0.84/0.84/demos/pagination.py para listas muy largas y poder ver distintas páginas

    #llamada a la función que muestre por pantalla los archivos de la planta 1
    #preguntar al launcher el resultado de las subastas en orden inverso al tiempo (sort)
    
    with st.container():
        left, centr, right = st.columns((2,1,1))
        with left:
            plant_machine = selectbox_with_default(
                'Plant Machine',
                df3['machines'])
            placeholdernew = centr.empty()
            placeholdernew.write('No Plant Machine Selected')
        
        
        if plant_machine != DEFAULT:

            directory_plant = turn_on_plant(plant_machine)
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
                plant_csv2 = convert_df(plant_df)

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

        

    #botón final de killall process y limpiar todo y botón de empezar todo? o ponerlo cada vez q seleccionas una plataforma?
    #minuto 50 grabacion

    #---> REPENSAR
    if shutdown:
    #eliminar carpetas?
        for mach in machines_parser:
            killall = "rsh "+str(mach)+' "killall python3"'
            out = subprocess.Popen(killall, stdout=None, stdin=None, stderr=None, \
                                close_fds=True, shell=True, universal_newlines = True)
