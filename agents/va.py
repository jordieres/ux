import time, datetime, sys, os, argparse,json, re
import socket, globals, random, pdb
import pandas as pd
import numpy as np
import operative_functions as asf
from spade import quit_spade
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour
from spade.template import Template
from spade.message import Message

global va_msg_log, auction_start, pre_auction_start

class VA(Agent):
    class VA_Behav(CyclicBehaviour):
        async def run(self):
            global process_df, va_status_var, my_full_name, coil_notified, \
                   va_status_started_at, stop_time, my_dir, wait_msg_time, \
                   va_data_df, conf_va_df, auction_df, fab_started_at, \
                   leeway, op_times_df, auction_start, va_to_tr_df, results_2,\
                   coil_msgs_df, medias_list, ip_machine, seq_va, number, \
                   list_stg_coils, va_msg_log, pre_auction_start, pending_au, \
                   coil_msgs_df2,coil_msgs_df3,post_auction_step, coil_notified, \
                   rep_pauction, all_auctions, price_energy_consumption, df_parameters_energy, winner_df, all_winner_df,winner_df_aux,i
            #
            #
            if va_status_var == "pre-auction":
                diff=(datetime.datetime.now()-pre_auction_start).total_seconds()
                rep_pauction = 0 # Tolerance of 5 to repetition in auctions.
                if self.act_qry('ask-coils','pre-auction') == 0 and diff > stept:
                    seq_va = seq_va + 1
                    auction_df.at[0, 'pre_auction_start'] = pre_auction_start
                    """Asks browser for active coils and locations"""
                    pre_auction_start = datetime.datetime.now()
                    [id_org,cl_agent] = await self.ask_coils()
                    curr = datetime.datetime.now()
                    globals.tosend.append({'idorg':id_org,'agnt_org': \
                                globals.gva_jid,'act':'ask-coils',\
                                'agnt_dst':globals.gbrw_jid,'dt':curr,\
                                'st':'pre-auction'})
                #
                """ Process the messages """
                msg_ag = await self.receive(timeout=wait_msg_time)
                if msg_ag:
                    recl = re.match(r'^c\d+',str(msg_ag.sender))
                    if 'BROW' in str(msg_ag.sender).upper():
                        cl_df = pd.read_json(msg_ag.body)
                        seqce = cl_df.loc[0,'seq']
                        [act,st] = self.ret_agnt(seqce)
                        if st == 'pre-auction' and act == 'ask-coils':                              
                            dact  = pd.read_json(cl_df.loc[0,'msg'])
                            glist = self.del_agnt(seqce,globals.tosend)
                            globals.tosend = glist
                            br_data_df = []
                            myfnam = (my_full_name.split('@')[0]).upper()
                            for k in dact.index:
                                res = re.match(dact.loc[k,'ph'].replace( \
                                                '\\',''),myfnam)
                                if res:
                                    if res.group(0) == myfnam:
                                        br_data_df.append(dact.loc[k,'id'])
                            #
                            if len(br_data_df) > 0: # There are coils waiting ...
                                auction_df.at[0, 'active_coils'] = br_data_df
                                #
                                # initial auction level
                                va_data_df.at[0, 'auction_level'] = 1  
                                va_data_df.at[0, 'bid_status'] = 'bid'
                                bid_mean = asf.bids_mean(medias_list)
                                va_data_df.at[0, 'bid_mean'] = float(bid_mean)
                                va_to_coils_df = asf.conf_medidas(va_data_df,conf_va_df)
                                # json to send to coils with auction info 
                                # including last temperatures
                                va_to_coils_json = va_to_coils_df.to_json()  
                                # Create a loop to inform of auctionable
                                # resource to willing to be fab coils.
                                jid_list = br_data_df
                                auction_df.at[0, 'number_preauction'] = auction_df.at[0, \
                                            'number_preauction'] + 1
                                number = int(auction_df.at[0, 'number_preauction'])
                                """Inform log """
                                va_log_msg = asf.send_va(my_full_name, number,  \
                                            va_data_df.at[0, 'bid_mean'],\
                                            va_data_df.at[0, 'auction_level'], jid_list)
                                va_log_json= va_log_msg.to_json(orient="records")
                                va_msg_log = asf.msg_to_log(va_log_json, my_dir)
                                await self.send(va_msg_log)
                                va_msg_to_coils = asf.va_msg_to(va_to_coils_json,\
                                            globals.gva_jid)
                                for z in jid_list:
                                    # Ask Coils
                                    id_org  = int(random.random()*10000)
                                    cl_agent= asf.rq_list(my_full_name,va_to_coils_df,\
                                            z,'invitation',id_org)
                                    cl_ans  = asf.contact_list_json(cl_agent,z)
                                    await self.send(cl_ans)
                                    curr = datetime.datetime.now()
                                    globals.tosend.append({'idorg':id_org,'agnt_org': \
                                            globals.gva_jid,'act':'invitation',\
                                            'agnt_dst':z,'dt':curr,'st':'pre-auction'})
                    elif recl is not None: # Means we have a coil answer ...
                        coil_jid = str(msg_ag.sender)
                        msg_snd_jid = coil_jid.split('/')[0]
                        cl_df = pd.read_json(msg_ag.body)
                        if cl_df.loc[0,'purpose'] == 'answer2invitation':
                            seqce = cl_df.loc[0,'seq']
                            coil_msg_df = pd.read_json(cl_df.loc[0,'msg'])
                            coil_msg_df.at[0,'coil_jid'] = msg_snd_jid
                            #coil_msgs_df = coil_msgs_df.append(coil_msg_df)  # received msgs
                            coil_msgs_df = pd.concat([coil_msgs_df,coil_msg_df], \
                                       axis=0,ignore_index=True)  # received msgs
                            coil_msgs_df.reset_index(drop=True,inplace=True)
                            glist = self.del_agnt(seqce,globals.tosend)
                            globals.tosend = glist
                            [mindt,ref] = self.min_dt('invitation','pre-auction')
                            if self.act_qry('invitation','pre-auction') == 0 or \
                                    (ref-mindt).total_seconds() > stept:
                                # Time for resolving the pre-auction
                                va_status_var = "auction"
                                auction_start = datetime.datetime.now() - \
                                                datetime.timedelta(seconds=2*stept)
                                auction_df.at[0, 'auction_start'] = None
                                coil_msgs_df2 = pd.DataFrame() # Preparing the auction

                        else:
                            """Inform log """
                            msgerr = cl_df.loc[0,'purpose']
                            va_msg_log_body = f'{my_full_name} receivef answer ' + \
                                    f'from {msg_snd_jid} a special msg: {msgerr}.'
                            va_df = pd.DataFrame()
                            va_df.loc[0,'purpose'] = 'inform_error'
                            va_df.loc[0,'msg'] = va_msg_log_body
                            va_msg_log = asf.msg_to_log(va_df.to_json(\
                                            orient="records"), my_dir)
                            await self.send(va_msg_log)
                    elif 'LAUN' in str(msg_ag.sender).upper():
                        # Message from Launcher requesting parameter update ...
                        msgl = pd.read_json(msg_ag.body)
                        msg_sender_jid = str(msg_ag.sender).split('/')[0]
                        if msgl.loc[0,'purpose'] == 'exit':
                            await self.ask_exit() # To log ...
                            self.kill() # To end.
                        elif msgl.loc[0,'purpose'] == 'search':
                            id_ag = msgl.loc[0,'seq']
                            cl_ag = asf.rq_list(my_full_name, all_auctions, \
                                         msg_sender_jid,'history',id_ag)
                            cnt_lst = asf.contact_list_json(cl_ag,msg_sender_jid)
                            await self.send(cnt_lst)
                        elif msgl.loc[0,'purpose'] == 'status_va':
                            #
                            # Answering current properties to browser.
                            st = pd.DataFrame([{\
                                 'Code':va_data_df.loc[0,'id'],\
                                 'From':va_data_df.loc[0,'oname'],\
                                 'msg': va_data_df.loc[0,'name'], \
                                 'Location': va_data_df.loc[0,'From'],
                                 'Capacity': va_data_df.loc[0,'budget'], \
                                 'purpose':'report', \
                                 'ancho':va_data_df.loc[0,'ancho'],\
                                 'espesor': va_data_df.loc[0,'espesor'],\
                                 'largo': va_data_df.loc[0,'largo'],\
                                 'parF': va_data_df.loc[0,'param_f'],\
                                 'artikel_gruppe': va_data_df.loc[0,'artikel_gruppe'],\
                                 'oel_sorte': va_data_df.loc[0,'oel_sorte'],\
                                 'assivieru_ngkz': va_data_df.loc[0,'assivieru_ngkz'],\
                                 'arkerung_mes': va_data_df.loc[0,'arkerung_mes'],\
                                 'sdate': va_data_df.loc[0,'ship_date'],\
                                 'status': va_status_var, \
                                 'parF': va_data_df.loc[0,'param_f'],\
                                 'sgrade': va_data_df.loc[0,'sgrade']}]).to_json(\
                                            orient="records")
                            rep= asf.msg_to_agnt(st,msgl.loc[0,'id'])
                            await self.send(rep)

            if va_status_var == "auction":
                diff=(datetime.datetime.now()-auction_start).total_seconds()
                if self.act_qry('counterbid','auction') == 0 and \
                        coil_msgs_df.shape[0] > 0 and diff > stept:
                    if auction_df.at[0, 'auction_start'] == None:
                        auction_df.at[0, 'auction_start'] = auction_start
                        auction_df.at[0, 'number_auction'] = auction_df.at[\
                                0, 'number_auction'] + 1
                    number = int(auction_df.at[0, 'number_auction'])
                    bid_list = coil_msgs_df.loc[:, 'id'].tolist()
                    bid_list_msg = str(bid_list)
                    va_data_df.at[0, 'auction_level'] = 2
                    """Inform log """
                    va_msg_body = asf.send_va(my_full_name, number, \
                                va_data_df.at[0, 'bid_mean'],\
                                va_data_df.at[0, 'auction_level'], bid_list_msg)
                    va_msg_bdjs = va_msg_body.to_json(orient="records")
                    va_msg_log = asf.msg_to_log(va_msg_bdjs, my_dir)
                    await self.send(va_msg_log)
                    """ Selecting coils with bid  >0  Coils interested """
                    coil_msgs_df = coil_msgs_df[coil_msgs_df['bid'] > 0]
                    coil_msgs_df = coil_msgs_df.reset_index(drop=True)
                    auction_df.at[0, 'auction_coils'] = [str(coil_msgs_df['id'\
                                ].to_list())]
                    jid_list = coil_msgs_df['id'].to_list()
                    if len(jid_list) > 0:
                        bid_coil = asf.va_bid_evaluation(coil_msgs_df, va_data_df,'bid',price_energy_consumption,df_parameters_energy, winner_df_aux)
                        bid_coil['bid_status'] = 'counterbid'
                        jid_list = bid_coil.loc[:, 'coil_jid'].tolist()
                        result = asf.va_result(bid_coil, jid_list,'bid')
                    for z in jid_list:
                        """Ask coils for counterbid"""
                        id_org  = int(random.random()*10000)
                        cl_agent= asf.rq_list(my_full_name,bid_coil,\
                                z,'counterbid',id_org)
                        cl_ans  = asf.contact_list_json(cl_agent,z)
                        await self.send(cl_ans)
                        curr = datetime.datetime.now()
                        globals.tosend.append({'idorg':id_org,'agnt_org': \
                                globals.gva_jid,'act':'counterbid',\
                                'agnt_dst':z,'dt':curr,'st':'auction'})
                #
                """ Process the messages """
                msg_ag = await self.receive(timeout=wait_msg_time)
                if msg_ag:
                    cl_df = pd.read_json(msg_ag.body)
                    lstids= [i['idorg'] for i in globals.tosend]
                    recl = re.match(r'^c\d+',str(msg_ag.sender).split('@')[0]) # Message from coils
                    if recl is not None and cl_df.loc[0,'seq'] in lstids: # Message from coil agents

                        coil_jid = str(msg_ag.sender)
                        msg_snd_jid = coil_jid.split('/')[0]
                        cl_df = pd.read_json(msg_ag.body)
                        if cl_df.loc[0,'purpose'] == 'answer2counterbid':
                            seqce = cl_df.loc[0,'seq']
                            coil_msg_df2 = pd.read_json(cl_df.loc[0,'msg'])
                            coil_msg_df2.at[0,'coil_jid'] = msg_snd_jid
                            #coil_msgs_df2 = coil_msgs_df2.append(coil_msg_df2)
                            coil_msgs_df2 = pd.concat([coil_msgs_df2,coil_msg_df2\
                                       ], axis=0, ignore_index=True)
                            coil_msgs_df2.reset_index(drop=True,inplace=True)
                            glist = self.del_agnt(seqce,globals.tosend)
                            globals.tosend = glist
                            [mindt,ref] = self.min_dt('counterbid','auction')
                            dlt = (ref-mindt).microseconds / 1.e+6
                            if len(globals.tosend) == 0 or dlt > 15:
                                # Time for resolving the auction
                                if coil_msgs_df2.shape[0] > 0:
                                    va_status_var = "post-auction"
                                    pending_au    = True
                                    post_auction_step = datetime.datetime.now() - \
                                        datetime.timedelta(seconds=2*stept)
                                    counterbid_coil = asf.va_bid_evaluation(coil_msgs_df2, \
                                                va_data_df,'counterbid',price_energy_consumption,\
                                                df_parameters_energy, winner_df_aux)
                                    """Inform coil of assignation and agree on assignation"""
                                    jid_list_2= counterbid_coil.loc[:,'coil_jid'].tolist()
                                    results_2 = asf.va_result(counterbid_coil, \
                                                jid_list_2,'counterbid')
                                    coil_notified = -1 # Not yet communicated
                                else:
                                    va_status_var == "stand-by"
                        else:
                            # print('What ???')
                            """Inform log """
                            msgerr = cl_df.loc[0,'purpose']
                            va_msg_log_body = f'{my_full_name} receivef answer ' + \
                                    f'from {msg_snd_jid} a special msg: {msgerr}.'
                            va_df = pd.DataFrame()
                            va_df.loc[0,'purpose'] = 'inform_error'
                            va_df.loc[0,'msg'] = va_msg_log_body
                            va_msg_log = asf.msg_to_log(va_df.to_json(\
                                     orient="records"), my_dir)
                            await self.send(va_msg_log)
                    elif 'LAUN' in str(msg_ag.sender).upper():
                        # Message from Launcher requesting parameter update ...
                        msgl = pd.read_json(msg_ag.body)
                        msg_sender_jid = str(msg_ag.sender).split('/')[0]
                        if msgl.loc[0,'purpose'] == 'exit':
                            await self.ask_exit() # To log ...
                            self.kill() # To end.
                        elif msgl.loc[0,'purpose'] == 'search':
                            #
                            id_ag = msgl.loc[0,'seq']
                            cl_ag = asf.rq_list(my_full_name, all_auctions, \
                                         msg_sender_jid,'history',id_ag)
                            cnt_lst = asf.contact_list_json(cl_ag,msg_sender_jid)
                            await self.send(cnt_lst)
                        elif msgl.loc[0,'purpose'] == 'status_va':
                            # Answering current properties to browser.
                            st = pd.DataFrame([{\
                                 'Code':va_data_df.loc[0,'id'],\
                                 'From':va_data_df.loc[0,'oname'],\
                                 'msg': va_data_df.loc[0,'name'], \
                                 'Location': va_data_df.loc[0,'From'],
                                 'Capacity': va_data_df.loc[0,'budget'], \
                                 'purpose':'report', \
                                 'ancho':va_data_df.loc[0,'ancho'],\
                                 'espesor': va_data_df.loc[0,'espesor'],\
                                 'largo': va_data_df.loc[0,'largo'],\
                                 'parF': va_data_df.loc[0,'param_f'],\
                                 'artikel_gruppe': va_data_df.loc[0,'artikel_gruppe'],\
                                 'oel_sorte': va_data_df.loc[0,'oel_sorte'],\
                                 'assivieru_ngkz': va_data_df.loc[0,'assivieru_ngkz'],\
                                 'arkerung_mes': va_data_df.loc[0,'arkerung_mes'],\
                                 'sdate': va_data_df.loc[0,'ship_date'],\
                                 'status': va_status_var, \
                                 'parF': va_data_df.loc[0,'param_f'],\
                                 'sgrade': va_data_df.loc[0,'sgrade']}]).to_json(\
                                            orient="records")
                            rep= asf.msg_to_agnt(st,msgl.loc[0,'id'])
                            await self.send(rep)
            #
            if va_status_var == "post-auction":
                diff=(datetime.datetime.now()-post_auction_step).total_seconds()
                if coil_notified < (coil_msgs_df2.shape[0]-1) and pending_au and \
                                coil_msgs_df2.shape[0] > 0  and diff > stept :
                    coil_notified    = coil_notified + 1
                    i = coil_msgs_df2.index[coil_notified]
                    """Evaluate extra bids and give a rating"""
                    va_data_df.loc[0, 'auction_level'] = 3  # third level
                    coil_jid_winner_f= results_2.loc[i,'Coil']
                    coil_jid_winner  = coil_jid_winner_f.split('@')[0]
                    winner_df = results_2.loc[i:i,:]
                    winner_df = winner_df.reset_index(drop=True)
                    winner_df_aux = winner_df
                    winner_df_aux.loc[0,'final_thickness'] = va_data_df.loc[0,'coil_thickness']

                    all_winner_df = pd.concat([all_winner_df,winner_df_aux])              #s
                    all_winner_df = all_winner_df.reset_index(drop=True)
                    profit    = float(results_2.loc[i, 'Profit'])
                    post_auction_step= datetime.datetime.now()   # Reset to follow up
                    # pdb.set_trace()
                    if profit >= 0.1:
                        winner_df.at[0, 'bid_status'] = 'acceptedbid'
                        va_data_df.at[0,'bid_status'] = 'acceptedbid'
                        va_data_df.loc[0,'accumulated_profit'] = va_data_df.loc[0,\
                                   'accumulated_profit'] + winner_df.loc[0, 'Profit']
                        """Inform log """
                        va_log_msg = asf.send_va(my_full_name, number, \
                                    va_data_df.at[0, 'bid_mean'],\
                                    va_data_df.at[0, 'auction_level'], \
                                    coil_jid_winner_f)
                        va_log_json= va_log_msg.to_json(orient="records")
                        va_msg_log = asf.msg_to_log(va_log_json, my_dir)
                        await self.send(va_msg_log)
                        """ Ask winner coil for OK """
                        id_org  = int(random.random()*10000)
                        cl_agent= asf.rq_list(my_full_name,winner_df,\
                                    coil_jid_winner,'confirm',id_org)
                        cl_ans  = asf.contact_list_json(cl_agent,coil_jid_winner_f)
                        await self.send(cl_ans)
                        curr = datetime.datetime.now()
                        globals.tosend.append({'idorg':id_org,'agnt_org': \
                                    globals.gva_jid,'act':'confirm',\
                                    'agnt_dst':coil_jid_winner,'dt':curr,\
                                    'st':'post-auction'})
                        pending_au = False
                    else:
                        """inform log of issue"""
                        va_msg_log_body = f'coil {coil_jid_winner_f} does not bring '
                        va_msg_log_body = va_msg_log_body + f'positive benefit to {my_full_name}'
                        va_msg_log_body = asf.inform_error(va_msg_log_body)
                        va_msg_log = asf.msg_to_log(va_msg_log_body, my_dir)
                        await self.send(va_msg_log)
                        id_org  = int(random.random()*10000)
                        cl_agent= asf.rq_list(my_full_name,winner_df,\
                                    coil_jid_winner_f,'notprofit',id_org)
                        cl_ans  = asf.contact_list_json(cl_agent,coil_jid_winner_f)
                        await self.send(cl_ans)
                elif coil_notified == coil_msgs_df2.shape[0]-1:
                    """ Post auction ended """
                    auction_df.at[0, 'number_auction_completed'] = auction_df.at[\
                                    0, 'number_auction_completed'] + 1
                    va_status_var = "stand-by"
                    coil_msgs_df = coil_msgs_df.drop(coil_msgs_df.index)
                    coil_msgs_df2= coil_msgs_df2.drop(coil_msgs_df2.index)
                    coil_msgs_df3= coil_msgs_df3.drop(coil_msgs_df3.index)
                    globals.tosend = []
                    globals.ret_dact= 0
                    pending_au = True
                    all_auctions = pd.concat([all_auctions, process_df],\
                                        ignore_index=True)

                    process_df = pd.DataFrame([], columns=['fab_start', \
                                'processing_time', 'start_auction_before', \
                                'start_next_auction_at','setup_speed', \
                                'coil_width','coil_length', 'coil_thickness'])
                    process_df.at[0, 'start_next_auction_at'] = datetime.datetime.now() + \
                                 datetime.timedelta(seconds=start_auction_before)
                    process_df.at[0,'setup_speed'] = 0.25 # Normal speed 15000 mm/min in m/s
                    process_df.at[0, 'start_auction_before'] = datetime.datetime.now()
                #
                msg_ag = await self.receive(timeout=wait_msg_time)
                if msg_ag:
                    recl = re.match(r'^c\d+',str(msg_ag.sender)) # Message from coils
                    if recl is not None: # Message from coil agents
                        coil_jid = str(msg_ag.sender)
                        msg_snd_jid = coil_jid.split('/')[0]
                        cl_df = pd.read_json(msg_ag.body)
                        seqce = cl_df.loc[0,'seq']
                        coil_msg_df3 = pd.read_json(cl_df.loc[0,'msg'])
                        #
                        if cl_df.loc[0, 'purpose'] == 'OKacceptedbid':
                            """Save winner information"""
                            auction_df.at[0, 'coil_ratings'] = [coil_msg_df3.to_dict(\
                                    orient="records")]  # Save information to auction df
                            """Calculate processing time"""
                            coil_msg_df3.loc[0,'setup_speed'] = speed
                            process_df = asf.set_process_df(process_df, coil_msg_df3, cl_df)
                            va_data_df.loc[0,'processing_time'] = process_df.loc[0,'processing_time']           #sergio 03/04
                            va_data_df.loc[0,'setup_speed'] = process_df.loc[0,'setup_speed']
                            """Inform log of assignation and auction KPIs"""
                            counterbid_win = coil_msg_df3.loc[0,'counterbid']
                            medias_list.append(float(counterbid_win))
                            auction_df.at[0, 'number_auction_completed'] = auction_df.at[\
                                        0, 'number_auction_completed'] + 1
                            number = int(auction_df.at[0, 'number_auction_completed'])
                            va_msg_log_body = asf.auction_va_kpis(va_data_df, coil_msg_df3,\
                                        auction_df, process_df, winner_df)
                            va_msg_log = asf.msg_to_log(va_msg_log_body.to_json(\
                                        orient="records"), my_dir)
                            va_msg_ganadores_log = asf.msg_to_log(all_winner_df.to_json(\
                                        orient="records"), my_dir)
                            # pdb.set_trace()
                            await self.send(va_msg_log)
                            await self.send(va_msg_ganadores_log)
                            pft     = winner_df.loc[0,'Profit']
                            dtw     = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            idord   = coil_msg_df3.loc[0,'id']
                            msg_str = f'AU_ENDED:{my_full_name}, auction:{number} '
                            msg_str = msg_str+f', winner:{idord}, price:{counterbid_win}'
                            msg_str = msg_str+f', profit:{pft}, date: {dtw}'
                            #
                            cl_msg_lbdy = asf.inform_log(my_full_name,\
                                        msg_str,globals.glog_jid)
                            cl_msg_lg_bd= cl_msg_lbdy.to_json(orient="records")
                            coil_msg_log= asf.msg_to_log(cl_msg_lg_bd, my_dir)
                            await self.send(coil_msg_log)
                            #
                            # Message to cancel other waiting coils ...
                            for k in coil_msg_df2.index:
                                if coil_msgs_df2.loc[k,'id'] != coil_msg_df3.loc[0,'id']:
                                    idc = coil_msgs_df2.loc[k,'id']
                                    tsnd= globals.tosend
                                    idt = self.find_qry('agnt_dst',idc.split('@')[0])
                                    if idt:
                                        glist = self.del_agnt(idt,globals.tosend)
                                        globals.tosend = glist
                            va_status_var = "stand-by"
                            coil_msgs_df = coil_msgs_df.drop(coil_msgs_df.index)
                            coil_msgs_df2= coil_msgs_df2.drop(coil_msgs_df2.index)
                            coil_msgs_df3= coil_msgs_df3.drop(coil_msgs_df3.index)
                            globals.tosend = []
                            globals.ret_dact= 0
                            pending_au = True
                            all_auctions = pd.concat([all_auctions, process_df],\
                                                ignore_index=True)
                            process_df = pd.DataFrame([], columns=['fab_start', \
                                        'processing_time', 'start_auction_before', \
                                        'start_next_auction_at','setup_speed', \
                                        'coil_width','coil_length', 'coil_thickness'])
                            process_df.at[0, 'start_next_auction_at'] = datetime.datetime.now() + \
                                         datetime.timedelta(seconds=start_auction_before)
                            process_df.at[0,'setup_speed'] = 0.25 # Normal speed 15000 mm/min in m/s
                            process_df.at[0, 'start_auction_before'] = datetime.datetime.now()
                        #
                        elif cl_df.loc[0, 'purpose'] == 'NOTacceptedbid':
                            msg_str = f'{my_full_name} rejected the auction'
                            msg_str = msg_str + f' number: {number}'
                            cl_msg_lbdy = asf.inform_log(my_full_name,\
                                                msg_str,globals.glog_jid)
                            cl_msg_lg_bd = cl_msg_lbdy.to_json(orient="records")
                            coil_msg_log = asf.msg_to_log(cl_msg_lg_bd, my_dir)
                            await self.send(coil_msg_log)
                            pending_au = True
                        else:
                            rep_pauction = rep_pauction + 1
                            if rep_pauction > 5:
                                va_status_var = 'pre-auction'
                                rep_pauction = 0
                        glist = self.del_agnt(seqce,globals.tosend)
                        globals.tosend = glist
                    elif 'LAUN' in str(msg_ag.sender).upper():
                        # Message from Launcher requesting parameter update ...
                        msgl = pd.read_json(msg_ag.body)
                        msg_sender_jid = str(msg_ag.sender).split('/')[0]
                        if msgl.loc[0,'purpose'] == 'exit':
                            await self.ask_exit() # To log ...
                            self.kill() # To end.
                        elif msgl.loc[0,'purpose'] == 'search':
                            id_ag = msgl.loc[0,'seq']
                            cl_ag = asf.rq_list(my_full_name, all_auctions, \
                                         msg_sender_jid,'history',id_ag)
                            cnt_lst = asf.contact_list_json(cl_ag,msg_sender_jid)
                            await self.send(cnt_lst)
                        elif msgl.loc[0,'purpose'] == 'status_va':
                            #
                            # Answering current properties to browser.
                            st = pd.DataFrame([{\
                                 'Code':va_data_df.loc[0,'id'],\
                                 'From':va_data_df.loc[0,'oname'],\
                                 'msg': va_data_df.loc[0,'name'], \
                                 'Location': va_data_df.loc[0,'From'],
                                 'Capacity': va_data_df.loc[0,'budget'], \
                                 'purpose':'report', \
                                 'ancho':va_data_df.loc[0,'ancho'],\
                                 'espesor': va_data_df.loc[0,'espesor'],\
                                 'largo': va_data_df.loc[0,'largo'],\
                                 'parF': va_data_df.loc[0,'param_f'],\
                                 'artikel_gruppe': va_data_df.loc[0,'artikel_gruppe'],\
                                 'oel_sorte': va_data_df.loc[0,'oel_sorte'],\
                                 'assivieru_ngkz': va_data_df.loc[0,'assivieru_ngkz'],\
                                 'arkerung_mes': va_data_df.loc[0,'arkerung_mes'],\
                                 'sdate': va_data_df.loc[0,'ship_date'],\
                                 'status': va_status_var, \
                                 'parF': va_data_df.loc[0,'param_f'],\
                                 'sgrade': va_data_df.loc[0,'sgrade']}]).to_json(\
                                            orient="records")
                            rep= asf.msg_to_agnt(st,msgl.loc[0,'id'])
                            await self.send(rep)
                        elif msgl.loc[0,'purpose'] == 'searchst':
                            #
                            id_ag = msgl.loc[0,'seq']
                            if va_status_var == 'pre-auction':
                                dff = coil_msgs_df
                            if va_status_var == 'auction':
                                dff = coil_msgs_df2
                            if va_status_var == 'post-auction':
                                dff = coil_msgs_df3
                            cl_ag = asf.rq_list(my_full_name, dff, \
                                         msg_sender_jid,'history',id_ag)
                            cnt_lst = asf.contact_list_json(cl_ag,msg_sender_jid)
                            await self.send(cnt_lst)
                #
                if diff > 160:
                    # After 10 mins without answer we drop off the auction
                    for k in coil_msgs_df2.index:
                        idc = coil_msgs_df2.loc[k,'id']
                        tsnd= globals.tosend
                        if len(tsnd) > 0:
                            ipc = self.find_qry('agnt_dst',idc.split('@')[0])
                            if ipc:
                                glist = self.del_agnt(ipc,globals.tosend)
                                globals.tosend = glist
                    va_status_var = "stand-by"
                    coil_msgs_df = coil_msgs_df.drop(coil_msgs_df.index)
                    coil_msgs_df2= coil_msgs_df2.drop(coil_msgs_df2.index)
                    coil_msgs_df3= coil_msgs_df3.drop(coil_msgs_df3.index)
                    globals.tosend = []
                    globals.ret_dact= 0
                    all_auctions = pd.concat([all_auctions, process_df],\
                                        ignore_index=True)
                    pending_au = True
                    process_df = pd.DataFrame([], columns=['fab_start', 'processing_time', \
                                 'start_auction_before', 'start_next_auction_at',\
                                'setup_speed', 'coil_width','coil_length', 'coil_thickness'])
                    process_df.at[0, 'start_next_auction_at'] = datetime.datetime.now() + \
                                 datetime.timedelta(seconds=start_auction_before)
                    process_df.at[0,'setup_speed'] = 0.25 # Normal speed 15000 mm/min in m/s
                    process_df.at[0, 'start_auction_before'] = datetime.datetime.now()
            #
            # stand-by status for VA is very useful. It changes to pre-auction.
            elif va_status_var == "stand-by":
                """ Starts next auction when there is some time left 
                    before current fab ends """
                if len(globals.tosend) == 0:
                    va_status_var = 'pre-auction'
                if len(globals.tosend) > 0:
                    act = globals.tosend[0]['act']
                    if act == 'invitation':
                        va_status_var = 'pre-auction'
                    elif act == 'counterbid':
                        va_status_var = 'auction'
            else:
                """inform log of status"""
                if 'auction' not in va_status_var:
                    va_inform_json = asf.inform_log_df(my_full_name, \
                            va_status_started_at, va_status_var, va_data_df\
                            ).to_json(orient="records")
                    va_msg_log = asf.msg_to_log(va_inform_json, my_dir)
                    await self.send(va_msg_log)
                    # print(' Unknown => '+ va_status_var)
                    # va_status_var = "stand-by"
        async def ask_exit(self):
            global va_status_var, number, coil_msgs_df, coil_msgs_df2,\
                        coil_msgs_df3, all_auctions, seq_va
            dtw = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            lcbs= []
            if coil_msgs_df.shape[0] > 0:
                lcbs= coil_msgs_df['id'].to_list()
            lcb2= []
            if coil_msgs_df2.shape[0] > 0:
                lcb2= coil_msgs_df2['id'].to_list()
            lcb3= []
            if coil_msgs_df3.shape[0] > 0:
                lcb3= coil_msgs_df3['id'].to_list()
            reg_cl = pd.DataFrame([{'id':globals.gva_jid,'status':va_status_var,\
                                    'auction':seq_va,'date':dtw,'coils_bid': lcbs,\
                                    'coils_cbid': lcb2,'coils_solv': lcb3,\
                                    'msg': 'Launcher requests to exit.'}])
            log_body    = asf.inform_log(my_full_name,\
                                reg_cl,globals.glog_jid)
            coil_msg_log = asf.msg_to_log(log_body, my_dir)
            await self.send(coil_msg_log)
            log_body    = asf.inform_log(my_full_name,\
                                all_auctions,globals.glog_jid)
            coil_msg_log = asf.msg_to_log(log_body, my_dir)
            await self.send(coil_msg_log)
            time.sleep(1)

        async def ask_coils(self):
            r = 'Request coil list'
            seqce    = int(random.random()*10000)
            rq_clist = asf.rq_list(my_full_name, r, globals.gbrw_jid,\
                                   'getlist',seqce)
            r_clist  = asf.contact_list_json(rq_clist,'browser')
            await self.send(r_clist)
            return([seqce,rq_clist])

        def ret_agnt(self,id_agnt):
            for idct in globals.tosend:
                if idct['idorg'] == id_agnt:
                    return([idct['act'], idct['st']])

        def del_agnt(self,id_agnt,glist):
            rem = -1
            for inum in range(len(glist)):
                idct = glist[inum]
                if idct['idorg'] == id_agnt:
                    rem = inum
            if rem > -1:
                glist.pop(rem)
            return(glist)

        def act_qry(self,act,st):
            i = 0
            for idct in globals.tosend:
                if idct['act'] == act and idct['st']==st:
                    i = i + 1
            return(i)

        def find_qry(self,field,val):
            for idct in globals.tosend:
                if str(val).upper() in str(idct[field]).upper():
                    return(idct['idorg'])
            return(None)

        def min_dt(self,act,st):
            low0 = datetime.datetime.now()
            low  = low0
            for idct in globals.tosend:
                if idct['act'] == act and idct['st'] == st:
                    low = min(idct['dt'],low)
            return([low,low0])

        async def on_end(self):
            va_msg_ended = asf.send_activation_finish(my_full_name, ip_machine, 'end')
            va_msg       = asf.msg_to_log(va_msg_ended, my_dir)
            await self.send(va_msg)
            await self.presence.unsubscribe(globals.gbrw_jid)
            await self.agent.stop()

        async def on_start(self):
            global va_msg_log, auction_start, pre_auction_start
            self.counter = 1
            coil_msgs_df  = pd.DataFrame()
            coil_msgs_df2 = pd.DataFrame()
            coil_msgs_df3 = pd.DataFrame()
            """Inform log """
            va_msg_start = asf.send_activation_finish(my_full_name, \
                    ip_machine, 'start')
            va_msg_log = asf.msg_to_log(va_msg_start, my_dir)
            await self.send(va_msg_log)
            va_activation_json = asf.activation_df(my_full_name,\
                    va_status_started_at,globals.gva_jid)
            va_msg_lg = asf.msg_to_log(va_activation_json, my_dir)
            await self.send(va_msg_lg)

    async def setup(self):
        # start_at = datetime.datetime.now() + datetime.timedelta(seconds=3)
        # b = self.VABehav(period=3, start_at=start_at)  # periodic sender
        b = self.VA_Behav()  # periodic sender
        template = Template()
        template.metadata = {"performative": "inform"}
        self.add_behaviour(b,template)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='wh parser')
    parser.add_argument('-an', '--agent_number', type=int, metavar='', required=False, default=8, help='agent_number: 8, 9, 10, 11, 12')
    parser.add_argument('-s', '--status', type=str, metavar='', required=False, default='pre-auction', help='status_var: pre-auction, auction, stand-by, Off')
    parser.add_argument('-st', '--stop_time', type=int, metavar='', required=False, default=84600, help='stop_time: time in seconds where agent')
    parser.add_argument('-sab', '--start_auction_before', type=int, metavar='', required=False, default=10, help='start_auction_before: seconds to start auction prior to current fab ends')
    parser.add_argument('-sd', '--speed', type=float, metavar='', required=False, default=0.25, help='VA speed. Example --speed 0.25 ')
    parser.add_argument('-w', '--wait_msg_time', type=int, metavar='', required=False, default=15, help='wait_msg_time: time in seconds to wait for a msg')
    #
    # MANAGEMENT DATA
    parser.add_argument('-u', '--user_name', type=str, metavar='', required=False, help='User to the XMPP platform')  # JOM 10/10
    parser.add_argument('-p', '--user_passwd', type=str, metavar='', required=False, help='Passwd for the XMPP platform')  # JOM 10/10
    parser.add_argument('-lag', '--log_agnt_id', type=str, metavar='', required=False, help='User ID for the log agent')
    parser.add_argument('-bag', '--brw_agnt_id', type=str, metavar='', required=False, help='User ID for the browser agent')

    args = parser.parse_args()
    my_dir = os.getcwd()
    my_name = os.path.basename(__file__)[:-3]
    my_full_name = str(args.user_name)
    wait_msg_time = args.wait_msg_time
    speed = args.speed
    va_status_started_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    va_status_refresh = datetime.datetime.now() + datetime.timedelta(seconds=5)
    va_status_var = args.status
    start_auction_before = args.start_auction_before
    """Save to csv who I am"""
    va_data_df = asf.set_agent_parameters(my_name, my_full_name,\
                 950,0.8,20000,40,'400',5,1,555,555,'X500','NWW1','')
    conf_va_df = va_data_df[['coil_width', 'coil_length', 'coil_thickness']]
    va_data_df['accumulated_profit'] = 0
    va_data_df.at[0,'wh_available'] = "K, L, M, N"
    auction_df = asf.auction_blank_df()
    auction_df.at[0, 'number_preauction'] = 0
    auction_df.at[0, 'number_auction'] = 0
    auction_df.at[0, 'number_auction_completed'] = 0
    all_winner_df = pd.DataFrame() 
    all_auctions = pd.DataFrame() # Storing history
    winner_df_aux=pd.DataFrame() ####################################################### Winner dataframe pero con el ancho pedido y el ancho que tenia
    winner_df = pd.DataFrame()  ######################################################## 
    process_df = pd.DataFrame([], columns=['fab_start', 'processing_time', \
                 'start_auction_before', 'start_next_auction_at',\
                'setup_speed', 'coil_width','coil_length', 'coil_thickness'])
    process_df.at[0, 'start_next_auction_at'] = datetime.datetime.now() + \
                 datetime.timedelta(seconds=start_auction_before)
    process_df.at[0,'setup_speed'] = 0.25 # Normal speed 15000 mm/min in m/s
    process_df.at[0, 'start_auction_before'] = datetime.datetime.now()
    medias_list = [140.]
    price_energy_consumption = 0.222 #euros/KWh   Sergio 25 feb
    aux_process_time=0
    ##################################################################################### Dataframe parameters excel 25 feb S
    ##################################################################################### Dataframe parameters excel 25 feb S
    index_va = ['va09', 'va10', 'va11', 'va11', 'va12', 'va12']
    df_parameters_energy=pd.DataFrame({'melting_code': ['*', '*', '1', '2','1','2'],
              'a': [-4335, -4335, -8081.22, -141,-6011.6, -3855.45],
              'b': [2.1, 2.1, 4.31, 3.27, 3.83, 2.4],
              'c': [5405.53, 5405.53, 6826.2, 5943.73, 6742.25, 901.87],
              'd': [191.27, 191.27, 240.12, 228.9, 195.85, 292.9],
              'e': [212.31, 212.31, 319.5, 348.29, 264.99, 238.68],
              'f': [9.44, 9.44, 12.68, 12.16, 11.74, 8.66]}, 
              index=index_va)
    ###############################################################
    fab_started_at = datetime.datetime.now()
    leeway = datetime.timedelta(minutes=int(2))
    op_times_df = pd.DataFrame([], columns=['AVG(ca_op_time)', 'AVG(tr_op_time)'])
    seq_va = int(0)
    list_stg_coils = ['K', 'L', 'M', 'N']
    stept  = 15 # Step of time considered as tuneable.

    "IP"
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip_machine = s.getsockname()[0]
    globals.IP = ip_machine

    """XMPP info"""
    if hasattr(args,'log_agnt_id') :
        glog_jid = args.log_agnt_id
        globals.glog_jid = glog_jid
    if hasattr(args,'brw_agnt_id') :
        gbrw_jid = args.brw_agnt_id
        globals.gbrw_jid = gbrw_jid
    if hasattr(args,'lhr_agnt_id') :
        glhr_jid = args.lhr_agnt_id
        globals.glhr_jid = glhr_jid
    if len(args.user_name) > 0:
        va_jid = args.user_name
    else:
        va_jid = asf.agent_jid(my_dir, my_full_name)
    if len(args.user_passwd) > 0:
        va_passwd = args.user_passwd
    else:
        va_passwd = asf.agent_passwd(my_dir, my_full_name)

    globals.gva_jid = va_jid
    globals.tosend  = []
    globals.ret_dact= 0
    pre_auction_start = datetime.datetime.now() - datetime.timedelta(\
                        seconds=90)
    coil_msgs_df    = pd.DataFrame()
    coil_msgs_df2   = pd.DataFrame()
    coil_msgs_df3   = pd.DataFrame()
    auction_start   = datetime.datetime.now()
    #
    va_agent = VA(va_jid, va_passwd)
    future   = va_agent.start(auto_register=True)
    future.result()
    #
    stop_time = datetime.datetime.now() + datetime.timedelta(\
                seconds=args.stop_time)
    while datetime.datetime.now() < stop_time:
        time.sleep(1)
    else:
        va_status_var = "off"
        va_agent.stop()
        quit_spade()
