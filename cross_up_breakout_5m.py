import websocket
import _thread
from datetime import datetime
import json
from binance.client import Client
import time
import psycopg2
import pickle
from ftplib import FTP

import numpy

import strategy

listSymbolMeanStd=[]
            
host = "..."
user = "..."
password = "..."

eventType="@kline_5m"
firstIndexcoin=289
lastIndexCoin=441
budgetquant=100
seuil=66	

listalready=[]
verroudb=_thread.allocate_lock()

volatility={}

def input(prixcoin,fee):
	global verroudb
	verroudb.acquire()
	while True:
				try:
					print(". .")
					mydb = psycopg2.connect( user = "...", password = "...", host = "localhost", port = "5432", database = "..." )
					mydb.autocommit = True
					time.sleep(1/1000000.0)
				except:
					continue
				break
	query="SELECT varirsi40,c79 FROM tradetable ORDER BY timestamp DESC limit 1;" # récupérer la marge sur portefeuille
	mycursor = mydb.cursor()
	mycursor.execute(query)
	myresult = mycursor.fetchall()
	s=""
	portfolio=float(s.join(myresult[0][0]))
	s=""
	trademargin=float(s.join(myresult[0][1]))  # marges cumulées
	mydb.close()
	verroudb.release()
	print("portfolio, trademargin ",portfolio,trademargin)
	if portfolio>budgetquant and (float(prixcoin)+float(fee))!=0:
			if float(prixcoin)>budgetquant:
				nbcoin=round((budgetquant/(float(prixcoin)+float(fee))),6)      # fraction d'un coin
			else:
				nbcoin=int(budgetquant/(float(prixcoin)+float(fee)))            # nombre de coins entier
			portfolio=round(portfolio-(nbcoin*(float(prixcoin)+float(fee))),6)  # solde portefeuille commun
			print(" achat ",portfolio,nbcoin)
			l=[]
			l.append(nbcoin)
			l.append(portfolio)
			l.append(round((nbcoin*(float(prixcoin)+float(fee))),6))	        # budget achat spécifique
			l.append(trademargin)
			return l.copy()
	return 0

def output(prixcoin,fee,nbcoin):    # fee ?
	global verroudb
	verroudb.acquire()
	while True:
				try:
					print(". .")
					mydb = psycopg2.connect( user = "...", password = "...", host = "localhost", port = "5432", database = "..." )
					mydb.autocommit = True
					time.sleep(1/1000000.0)
				except:
					continue
				break
	query="SELECT varirsi40,c79 FROM tradetable ORDER BY timestamp DESC limit 1;" # récupérer la marge sur portefeuille
	mycursor = mydb.cursor()
	mycursor.execute(query)
	myresult = mycursor.fetchall()
	s=""
	portfolio=float(s.join(myresult[0][0]))
	s=""
	trademargin=float(s.join(myresult[0][1]))  # marges cumulées
	mydb.close()
	verroudb.release()
	print("vente, portfolio, trademargin ",portfolio,trademargin)
	portfolio=round(portfolio+(nbcoin*(float(prixcoin)+float(fee))),6)
	print("vente, portfolio, trademargin, nbcoin ",portfolio,trademargin,nbcoin)
	l=[]
	l.append(nbcoin)
	l.append(portfolio)
	l.append(trademargin)
	return l.copy()

def info_():
	api_key = "..."
	api_secret = "..."
	client = Client(api_key, api_secret)
	exchange_info = client.get_exchange_info()
	lexcinfo=[]
	linfo=[]
	i=0
	for s in exchange_info['symbols']:
		if s['symbol'].lower().endswith("usdt"):
			linfo.append(s['symbol'].lower())
			if i>=firstIndexcoin: lexcinfo.append(s['symbol'].lower()+eventType)
			if i>=lastIndexCoin: break
			i+=1
	req_='{ "method": "SUBSCRIBE", "params": ' + str(lexcinfo).replace("'","\"") + ', "id": 1}'
	return req_

requete_=info_()

def alreadyin(tuplalready):
        for la in listalready:
            if la==tuple(tuplalready):
                return 1
        return 0

def ws_message (ws,message):
    m=json.loads(message)
    print(" . ")
    if m['e']=='kline':
            tuplalready=(m['k']['t'],m['k']['T'],m['s'])
            b9=alreadyin(tuplalready)
            if b9!=1:        
                listalready.append(tuplalready)
                if len(listalready)>lastIndexCoin*2:
                    del listalready[0]
                #print(m['s'],m['E'],m['k']['q'],m['k']['c'])
                _thread.start_new_thread(compute,(m['E'],m['s'],m['k']['c'],m['k']['v'],m['k']['n'],m['k']['q'],m['k']['V'],m['k']['Q'],))
    if m['e']=='trade':
            #print(m['s'],m['E'],m['q'],m['p'])
            compute(m['s'],m['E'],m['q'],m['p'])

def ws_open(ws):
	ws.send(requete_)
	print("ws_open : ",requete_)

def ws_thread(*args):
	ws = websocket.WebSocketApp("wss://stream.binance.com:9443/ws", on_open = ws_open, on_message = ws_message)
	ws.run_forever()
			

def insertCoin(listToDB):
	global verroudb
	i=0
	for x in listToDB:
		if len(str(x))>= 27: listToDB[i]=str(x)[:27]
		i+=1
	mydb=0
	verroudb.acquire()
	while True:
		try:
			print(". .")
			mydb = psycopg2.connect( user = "...", password = "...", host = "localhost", port = "5432", database = "..." )
			mydb.autocommit = True
			time.sleep(1/1000000.0)
		except:
			continue
		break
	mycursor = mydb.cursor()
	sql = "INSERT INTO coin" + listToDB[0] + " ( coin , timestamp , weight , price , datetime , sma21rsi40 , ema21rsi40 ,  rsi14 , rsi40 , ema21cours , varirsi40 ,  sma7 , varsma7 , signvarsma7 , ranksma7 , rsi40crossema21rsi40 , sma8 , varsma8 , signvarsma8 , ranksma8 , varranksma8 , sma9 , varsma9 , signvarsma9 , ranksma9 , varranksma9 , sma20 , varsma20 , signvarsma20 , ranksma20 , varranksma20 , sma50 , varsma50 , signvarsma50 , ranksma50 , varranksma50 , sma200 , varsma200 , signvarsma200 , ranksma200 , booleenbreakout , pricetwin , varprice , signvarsmaprice , rankprice , varrankprice , fee , transactionencours , rsi7  , ema7rsi7  , rsi7crossema7rsi7 , rsi100 , sma50rsi100 , ema50rsi100 , rsi100crosssma50rsi100 , rsi100crossema50rsi100 , rsi200 , sma200rsi200 , ema200rsi200 , rsi200crosssma200rsi200 , rsi200crossema200rsi200 , ema100rsi100 , rsi100crossema100rsi100 , prixachat , trade , trade1 , trade2 , trade3 , rsi1200 , sma1200rsi1200 , rsi600 , sma600rsi600 , rsi1200crosssma1200rsi1200 , rsi600crosssma600rsi600, c74, c75, c76, c77, c78, c79, c80, c81, c82, c83, c84, c85, c86, c87, c88, c89, c90, c91, c92, c93, c94, c95, c96, c97, c98, c99) VALUES ( %s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s , %s, %s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s , %s, %s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s , %s, %s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s , %s, %s,	%s,	%s,	%s,	%s,	%s )"
	val = (listToDB[0], listToDB[1], listToDB[2], listToDB[3], listToDB[4], listToDB[5], listToDB[6], listToDB[7], listToDB[8], listToDB[9], listToDB[10], listToDB[11], listToDB[12], listToDB[13], listToDB[14], listToDB[15], listToDB[16], listToDB[17], listToDB[18], listToDB[19], listToDB[20], listToDB[21], listToDB[22], listToDB[23], listToDB[24], listToDB[25], listToDB[26], listToDB[27], listToDB[28], listToDB[29], listToDB[30], listToDB[31], listToDB[32], listToDB[33], listToDB[34], listToDB[35], listToDB[36], listToDB[37], listToDB[38], listToDB[39], listToDB[40], listToDB[41], listToDB[42], listToDB[43], listToDB[44], listToDB[45], listToDB[46], listToDB[47], listToDB[48], listToDB[49], listToDB[50], listToDB[51], listToDB[52], listToDB[53], listToDB[54], listToDB[55], listToDB[56], listToDB[57], listToDB[58], listToDB[59], listToDB[60], listToDB[61], listToDB[62], listToDB[63], listToDB[64], listToDB[65], listToDB[66], listToDB[67], listToDB[68], listToDB[69], listToDB[70], listToDB[71], listToDB[72], listToDB[73], listToDB[74], listToDB[75], listToDB[76], listToDB[77], listToDB[78], listToDB[79], listToDB[80], listToDB[81], listToDB[82], listToDB[83], listToDB[84], listToDB[85], listToDB[86], listToDB[87], listToDB[88], listToDB[89], listToDB[90], listToDB[91], listToDB[92], listToDB[93], listToDB[94], listToDB[95], listToDB[96], listToDB[97], listToDB[98], listToDB[99])
	mycursor.execute(sql, val)
	mydb.commit()
	mydb.close()
	verroudb.release()

def insertTrade(listToDB):
	global verroudb
	#i=0
	#for x in listToDB:
		#if len(str(x))>= 27: listToDB[i]=str(x)[:27]
		#i+=1
	mydb=0
	verroudb.acquire()
	while True:
		try:
			print("...")
			mydb = psycopg2.connect( user = "...", password = "...", host = "localhost", port = "5432", database = "..." )
			mydb.autocommit = True
			time.sleep(1/1000000.0)
		except:
			continue
		break
	mycursor = mydb.cursor()
	sql = "INSERT INTO tradetable ( coin , timestamp , weight , price , datetime , sma21rsi40 , ema21rsi40 ,  rsi14 , rsi40 , ema21cours , varirsi40 ,  sma7 , varsma7 , signvarsma7 , ranksma7 , rsi40crossema21rsi40 , sma8 , varsma8 , signvarsma8 , ranksma8 , varranksma8 , sma9 , varsma9 , signvarsma9 , ranksma9 , varranksma9 , sma20 , varsma20 , signvarsma20 , ranksma20 , varranksma20 , sma50 , varsma50 , signvarsma50 , ranksma50 , varranksma50 , sma200 , varsma200 , signvarsma200 , ranksma200 , booleenbreakout , pricetwin , varprice , signvarsmaprice , rankprice , varrankprice , fee , transactionencours , rsi7  , ema7rsi7  , rsi7crossema7rsi7 , rsi100 , sma50rsi100 , ema50rsi100 , rsi100crosssma50rsi100 , rsi100crossema50rsi100 , rsi200 , sma200rsi200 , ema200rsi200 , rsi200crosssma200rsi200 , rsi200crossema200rsi200 , ema100rsi100 , rsi100crossema100rsi100 , prixachat , trade , trade1 , trade2 , trade3 , rsi1200 , sma1200rsi1200 , rsi600 , sma600rsi600 , rsi1200crosssma1200rsi1200 , rsi600crosssma600rsi600, c74, c75, c76, c77, c78, c79, c80, c81, c82, c83, c84, c85, c86, c87, c88, c89, c90, c91, c92, c93, c94, c95, c96, c97, c98, c99) VALUES ( %s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s , %s, %s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s , %s, %s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s , %s, %s,	%s,	%s,	%s,	%s,	%s,	%s,	%s,	%s , %s, %s,	%s,	%s,	%s,	%s,	%s )"
	val = (listToDB[0], listToDB[1], listToDB[2], listToDB[3], listToDB[4], listToDB[5], listToDB[6], listToDB[7], listToDB[8], listToDB[9], listToDB[10], listToDB[11], listToDB[12], listToDB[13], listToDB[14], listToDB[15], listToDB[16], listToDB[17], listToDB[18], listToDB[19], listToDB[20], listToDB[21], listToDB[22], listToDB[23], listToDB[24], listToDB[25], listToDB[26], listToDB[27], listToDB[28], listToDB[29], listToDB[30], listToDB[31], listToDB[32], listToDB[33], listToDB[34], listToDB[35], listToDB[36], listToDB[37], listToDB[38], listToDB[39], listToDB[40], listToDB[41], listToDB[42], listToDB[43], listToDB[44], listToDB[45], listToDB[46], listToDB[47], listToDB[48], listToDB[49], listToDB[50], listToDB[51], listToDB[52], listToDB[53], listToDB[54], listToDB[55], listToDB[56], listToDB[57], listToDB[58], listToDB[59], listToDB[60], listToDB[61], listToDB[62], listToDB[63], listToDB[64], listToDB[65], listToDB[66], listToDB[67], listToDB[68], listToDB[69], listToDB[70], listToDB[71], listToDB[72], listToDB[73], listToDB[74], listToDB[75], listToDB[76], listToDB[77], listToDB[78], listToDB[79], listToDB[80], listToDB[81], listToDB[82], listToDB[83], listToDB[84], listToDB[85], listToDB[86], listToDB[87], listToDB[88], listToDB[89], listToDB[90], listToDB[91], listToDB[92], listToDB[93], listToDB[94], listToDB[95], listToDB[96], listToDB[97], listToDB[98], listToDB[99])
	mycursor.execute(sql, val)
	mydb.commit()
	mydb.close()
	verroudb.release()
 
def myfunc(result):
	return result[1]
  
def compute(timestamp,coin,price,v_,n_,q_,V_,Q_):
	global verroudb
	listToDB=[]
	#E,s,c,v,n,q,V,Q
	for i in range(100):
			listToDB.append(0)

	timest = float(timestamp)/1000
	#print(timestamp)	
	timest=str(datetime.fromtimestamp(timest))

	liquidite_=float(v_)
	if float(q_)!=0:
		liquidite_=round((float(v_)/float(q_)),6)	# v_/q_ liquidité

	listToDB[0]=coin
	listToDB[1]=timest
	listToDB[2]=liquidite_
	listToDB[3]=round(float(price),6)
	listToDB[4]=round((float(v_)),6)
	listToDB[5]=round((float(q_)),6)
	if float(n_)!=0 : 
		listToDB[4]=round((float(v_)/float(n_)),6)      # ratio liquidité base
		listToDB[5]=round((float(q_)/float(n_)),6)      # ratio liquidité devise
	listToDB[25]=seuil
	listToDB[41]=round(float(price),6)
	listToDB[46]=0.001  #0.1% fee
	listToDB[54]=round((float(V_)*float(Q_)),6)

	mydb=0
	verroudb.acquire()
	while True:
		try:
			mydb = psycopg2.connect( user = "...", password = "...", host = "localhost", port = "5432", database = "..." )
			mydb.autocommit = True
			time.sleep(1/1000000.0)
		except:
			continue
		break
	mycursor = mydb.cursor()
	table_name="SELECT * FROM coin"+coin+" ORDER BY timestamp DESC LIMIT 200 ;" #1200
	mycursor.execute(table_name)
	ultat=mycursor.fetchall()
	mydb.close()
	verroudb.release()
	myresult=[]
	myresult.append(tuple(listToDB))
	myresult+=ultat
	myresult.sort(key=myfunc)
    
	try:
		listToDB[63]=round(float(ultat[0][63]),6)	#listToDB.append(ultat[0][63])
	except:
		listToDB[63]=0				#listToDB.append(-1)

	delta=14
	epsilon=1
	theta=40
	epsilony=2
	b100=b200=b14=b40=b7=False
	mmeh=mmeb=0
	lrsi14hausses=[]
	lrsi14baisses=[]
	lrsi40hausses=[]
	lrsi40baisses=[]
	lrsi7hausses=[]
	lrsi7baisses=[]
	lrsi100hausses=[]
	lrsi100baisses=[]
	lrsi200hausses=[]
	lrsi200baisses=[]
	rsi100=rsi200=rsi=rsitheta=rsi7=0 #rsi correspond à rsi14
	ema100rsi100=ema50rsi100=ema200rsi200=em7rsi7=ema21rsi40=ema21=mma9=mma8=mma7=mma20=mma50=mma200=0
	liquidite=0
	m=0
	lstat=[]
	
	if len(myresult)>=200: #1200
		for x in myresult:
				nrsih=nrsib=mhb=rsi=0
				nrsihtheta=nrsibtheta=mhbtheta=rsitheta=0
			
				if m>0:                 #1200-200 = 1000        0
					mma200+=float(x[3])
					
					nrsi200=float(x[3])-float(y[3])	#x[3] price
					#print("hausse ou baisse : "+str(nrsi200))
					if nrsi200>=0:
						lrsi200hausses.append(nrsi200)
						lrsi200baisses.append(0)
					else:
						lrsi200baisses.append(-nrsi200)
						lrsi200hausses.append(0)
					
					ema200rsi200+=float(x[56])	# rsi200
					
					lstat.append(float(x[3]))
					#moyenne=(x[3]+moyenne*(m-1))/m
				
				if m>100:               #1200-100 = 1100        100
					nrsi100=float(x[3])-float(y[3])	#x[3] price
					#print("hausse ou baisse : "+str(nrsi100))
					if nrsi100>=0:
						lrsi100hausses.append(nrsi100)
						lrsi100baisses.append(0)
					else:
						lrsi100baisses.append(-nrsi100)
						lrsi100hausses.append(0)
					
					ema100rsi100+=float(x[51])	# rsi100
                    
				if m>150:               #1200-50 = 1150         150
					ema50rsi100+=float(x[51])	# rsi100
					mma50+=float(x[3])
					
				if m>(200-theta):       #1200-theta             200-theta
					nrsitheta=float(x[3])-float(y[3])	#x[3] price
					#print("hausse ou baisse : "+str(nrsitheta))
					if nrsitheta>=0:
						lrsi40hausses.append(nrsitheta)
						lrsi40baisses.append(0)
					else:
						lrsi40baisses.append(-nrsitheta)
						lrsi40hausses.append(0)
						
				if m>179:               #1200-21 = 1179         179
					ema21+=float(x[3])          # ema21cours
					ema21rsi40+=float(x[8])	# rsi40 ou rsitheta
					
				if m>180:               #1200-20 = 1180         180
					mma20+=float(x[3])
					
				if m>(200-delta):       #1200-delta             200-delta
					nrsi=float(x[3])-float(y[3])	#x[3] price
					#print("hausse ou baisse : "+str(nrsi))
					if nrsi>=0:
						lrsi14hausses.append(nrsi)
						lrsi14baisses.append(0)
					else:
						lrsi14baisses.append(-nrsi)
						lrsi14hausses.append(0)
				
				if m>191:               #1200-9 = 1191          191
					mma9+=float(x[3])

				if m>192:               #1200-8 = 1192          192
					mma8+=float(x[3])

				if m>193:               #1200-7 = 1193          193
					mma7+=float(x[3])
					
					nrsi7=float(x[3])-float(y[3])	#x[3] price
					#print("hausse ou baisse : "+str(nrsitheta))
					if nrsi7>=0:
						lrsi7hausses.append(nrsi7)
						lrsi7baisses.append(0)
					else:
						lrsi7baisses.append(-nrsi7)
						lrsi7hausses.append(0)
					
					em7rsi7+=float(x[48])	# rsi7
					liquidite+=float(x[2])
					
						
				if m>=(200):            #1200                   200
					nrsih=nrsib=0
					for mm in range(len(lrsi14hausses)):	#range(m-delta,m):
						nrsih=float(lrsi14hausses[mm])+nrsih					
						nrsib=float(lrsi14baisses[mm])+nrsib					
						derncoursh=lrsi14hausses[mm]
						derncoursb=lrsi14baisses[mm]
					if b14==False:
						b14=True
						mmeh=nrsih=nrsih/delta
						mmeb=nrsib=nrsib/delta
					else:
						mmeh=nrsih=(mmeh*(1-(epsilon/(delta+epsilon-1))))+((epsilon/(delta+epsilon-1))*derncoursh)
						mmeb=nrsib=(mmeb*(1-(epsilon/(delta+epsilon-1))))+((epsilon/(delta+epsilon-1))*derncoursb)
					mhb=0
					if nrsib!=0:
						mhb=nrsih/nrsib
					else:
						mhb=nrsih
					rsi=100-(100/(1+mhb))


					nrsihtheta=nrsibtheta=0
					for mmtheta in range(len(lrsi40hausses)):	#range(m-delta,m):
						nrsihtheta=float(lrsi40hausses[mmtheta])+nrsihtheta					
						nrsibtheta=float(lrsi40baisses[mmtheta])+nrsibtheta					
						derncourshtheta=lrsi40hausses[mmtheta]
						derncoursbtheta=lrsi40baisses[mmtheta]
					if b40==False:
						b40=True
						mmehtheta=nrsihtheta=nrsihtheta/theta
						mmebtheta=nrsibtheta=nrsibtheta/theta
					else:
						mmehtheta=nrsihtheta=(mmehtheta*(1-(epsilon/(theta+epsilon-1))))+((epsilon/(theta+epsilon-1))*derncourshtheta)
						mmebtheta=nrsibtheta=(mmebtheta*(1-(epsilon/(theta+epsilon-1))))+((epsilon/(theta+epsilon-1))*derncoursbtheta)
					mhbtheta=0
					if nrsibtheta!=0:
						mhbtheta=nrsihtheta/nrsibtheta
					else:
						mhbtheta=nrsihtheta
					rsitheta=100-(100/(1+mhbtheta))


					nrsih7=nrsib7=0
					for mm7 in range(len(lrsi7hausses)):
						nrsih7=float(lrsi7hausses[mm7])+nrsih7					
						nrsib7=float(lrsi7baisses[mm7])+nrsib7					
						derncoursh7=lrsi7hausses[mm7]
						derncoursb7=lrsi7baisses[mm7]
					if b7==False:
						b7=True
						mmeh7=nrsih7=nrsih7/7
						mmeb7=nrsib7=nrsib7/7
					else:
						mmeh7=nrsih7=(mmeh7*(1-(epsilon/(7+epsilon-1))))+((epsilon/(7+epsilon-1))*derncoursh7)
						mmeb7=nrsib7=(mmeb7*(1-(epsilon/(7+epsilon-1))))+((epsilon/(7+epsilon-1))*derncoursb7)
					mhb7=0
					if nrsib7!=0:
						mhb7=nrsih7/nrsib7
					else:
						mhb7=nrsih7
					rsi7=100-(100/(1+mhb7))
					

					nrsih200=nrsib200=0
					for mm200 in range(len(lrsi200hausses)):
						nrsih200=float(lrsi200hausses[mm200])+nrsih200					
						nrsib200=float(lrsi200baisses[mm200])+nrsib200					
						derncoursh200=lrsi200hausses[mm200]
						derncoursb200=lrsi200baisses[mm200]
					if b200==False:
						b200=True
						mmeh200=nrsih200=nrsih200/200
						mmeb200=nrsib200=nrsib200/200
					else:
						mmeh200=nrsih200=(mmeh200*(1-(epsilon/(200+epsilon-1))))+((epsilon/(200+epsilon-1))*derncoursh200)
						mmeb200=nrsib200=(mmeb200*(1-(epsilon/(200+epsilon-1))))+((epsilon/(200+epsilon-1))*derncoursb200)
					mhb200=0
					if nrsib200!=0:
						mhb200=nrsih200/nrsib200
					else:
						mhb200=nrsih200
					rsi200=100-(100/(1+mhb200))
					

					nrsih100=nrsib100=0
					for mm100 in range(len(lrsi100hausses)):
						nrsih100=float(lrsi100hausses[mm100])+nrsih100					
						nrsib100=float(lrsi100baisses[mm100])+nrsib100					
						derncoursh100=lrsi100hausses[mm100]
						derncoursb100=lrsi100baisses[mm100]
					if b100==False:
						b100=True
						mmeh100=nrsih100=nrsih100/100
						mmeb100=nrsib100=nrsib100/100
					else:
						mmeh100=nrsih100=(mmeh100*(1-(epsilon/(100+epsilon-1))))+((epsilon/(100+epsilon-1))*derncoursh100)
						mmeb100=nrsib100=(mmeb100*(1-(epsilon/(100+epsilon-1))))+((epsilon/(100+epsilon-1))*derncoursb100)
					mhb100=0
					if nrsib100!=0:
						mhb100=nrsih100/nrsib100
					else:
						mhb100=nrsih100
					rsi100=100-(100/(1+mhb100))
				y=x
				m+=1

	mma9/=9
	mma8/=8
	mma7/=7
	mma20/=20
	mma50/=50
	mma200/=200
	ema21=(ema21+float(listToDB[41])*(epsilony-1))/(21+epsilony-1)
	listToDB[9]=round(ema21,6)                                                  # ema21cours
	listToDB[21]=str(round(mma9,6))
	listToDB[16]=str(round(mma8,6))
	listToDB[11]=str(round(mma7,6))
	listToDB[26]=str(round(mma20,6))
	listToDB[31]=str(round(mma50,6))
	listToDB[36]=str(round(mma200,6))
	listToDB[7]=str(round(rsi,6))		                                        # rsi14 (rsimma dans sql)
	listToDB[8]=round(rsitheta,6)		                                        # rsi40 =rsi40/5mn
	ema21rsi40=(ema21rsi40+float(listToDB[8])*epsilony)/(21+epsilony-1)
	listToDB[6]=round(ema21rsi40,6)	                                            # ema21rsi40 =ema21/rsi40/5mn
	listToDB[48]=round(rsi7,6)			                                        # rsi7 (rsi7 dans sql)
	em7rsi7=(em7rsi7+float(listToDB[48])*epsilony)/(7+epsilony-1)	            # 7 !
	listToDB[49]=round(em7rsi7,6)                                               # ema7rsi7
	
	listToDB[47]=round(((liquidite+float(listToDB[2]))/7),6)                    # sma liquidite (achat si 2 > 47)
	
	listToDB[56]=round(rsi200,6)			                                    # rsi200 = rsi40/30mn
	sma200rsi200=(ema200rsi200+float(listToDB[56]))/(200)
	listToDB[57]=round(sma200rsi200,6)
	ema200rsi200=(ema200rsi200+float(listToDB[56])*epsilony)/(200+epsilony-1)	# 200 !
	listToDB[58]=round(ema200rsi200,6)	                                        # ema200rsi200 = ema40/rsi40/30mn
	
	listToDB[51]=round(rsi100,6)			                                    # rsi100 = rsi40/15mn
	ema50rsi100=(ema50rsi100+float(listToDB[51])*epsilony)/(50+epsilony-1)	    # 50 !
	listToDB[53]=round(ema50rsi100,6)	                                        # ema50rsi100   =ema21/rsi40/15mn
	ema100rsi100=(ema100rsi100+float(listToDB[51])*epsilony)/(100+epsilony-1)	# 100 ! 
	listToDB[61]=round(ema100rsi100,6)                                          # ema100rsi100  =ema40/rsi40/15mn
	
    # analyse de la liquidité
	boolliquid=0
	try:
		if ultat[0][3] is not None and ultat[0][4] is not None and ultat[0][5] is not None and ultat[0][54] is not None:
			if listToDB[2] >= listToDB[47] and listToDB[4]>=float(ultat[0][4]) and listToDB[5]>=float(ultat[0][5]) and listToDB[54]>=float(ultat[0][54]):
				boolliquid=1
	except IndexError:
		print("IndexError 3 4 5 54")
		boolliquid=0
		
    # recherche croisements entre rsi40 ema21rsi40 et si rsi40>ema21rsi40 (theta) : rsi40crossema21rsi40 
	try:
		if ultat[0][8] is not None and ultat[0][6] is not None and (((listToDB[8]-listToDB[6]))*(float(ultat[0][8])-float(ultat[0][6])))<0:
			if listToDB[8]>listToDB[6]:
				listToDB[15]="incrossup5"
			else:
				listToDB[15]="outcrossdown5"
		else:
			listToDB[15]="_"
	except IndexError:
		listToDB[15]="IndexError 6 8"
	#print(listToDB[15])
	
	# recherche croisements entre rsi7 ema7rsi7 et si rsi7>ema7rsi7
	try:
		if ultat[0][48] is not None and ultat[0][49] is not None and(((listToDB[48]-listToDB[49]))*(float(ultat[0][48])-float(ultat[0][49])))<0:
			if listToDB[48]>listToDB[49]:
				listToDB[50]="cross_up_7"
			else:
				listToDB[50]="cross_down_7"
		else:
			listToDB[50]="_"
	except IndexError:
		listToDB[50]="IndexError 48 49"
	#print(listToDB[50])

	# recherche croisements entre rsi200 ema200rsi200 et si rsi200>ema200rsi200
	try:
		if ultat[0][56] is not None and ultat[0][58] is not None and (((listToDB[56]-listToDB[58]))*(float(ultat[0][56])-float(ultat[0][58])))<0:
			if listToDB[56]>listToDB[58]:
				listToDB[60]="incrossup30m"
				print("incrossup30m")
			else:
				listToDB[60]="outcrossdown30"
		else:
			listToDB[60]="_"
	except IndexError:
		listToDB[60]="IndexError 56 58"

	# recherche croisements entre rsi100 ema50rsi100 et si rsi100>ema50rsi100
	try:
		if ultat[0][51] is not None and ultat[0][53] is not None and (((listToDB[51]-listToDB[53]))*(float(ultat[0][51])-float(ultat[0][53])))<0:
			if listToDB[51]>listToDB[53]:
				listToDB[55]="incrossup15"
			else:
				listToDB[55]="outcrossdown15"
		else:
			listToDB[55]="_"
	except IndexError:
		listToDB[55]="IndexError 51 53"
	
    # recherche croisements entre rsi100 ema100rsi100 et si rsi100>ema100rsi100
	try:
		if ultat[0][51] is not None and ultat[0][61] is not None and (((listToDB[51]-listToDB[61]))*(float(ultat[0][51])-float(ultat[0][61])))<0:
			if listToDB[51]>listToDB[61]:
				listToDB[62]="incrossup15m"
				print("incrossup15m")
			else:
				listToDB[62]="outcrossdown10"
		else:
			listToDB[62]="_"
	except IndexError:
		listToDB[62]="IndexError 51 61"

    # listToDB[12] : calcul variations n - n-1 : sma20-sma20n-1 sma50-sma50n-1 ... le cours monte
	try:
			listToDB[12]=round(float(listToDB[11])-float(ultat[0][11]),6)
			listToDB[42]=round(float(listToDB[41])-float(ultat[0][41]),6)
	except IndexError:
			listToDB[12]=round(float(listToDB[11]),6)
			listToDB[42]=round(float(listToDB[41]),6)
			
    # listToDB[43] : calcul signe now / before
	try:
			if (float(listToDB[42])*float(ultat[0][42]))<0:
				if (float(listToDB[42])>0):
					listToDB[43]="var_sign_up"     # signe variations n - n-1 : sma20-sma20n-1 sma50-sma50n-1 ...
				elif (float(listToDB[42])==0):
					listToDB[43]="_"              # signe variations n - n-1 : sma20-sma20n-1 sma50-sma50n-1 ...
				else:
					listToDB[43]="var_sign_down"    # signe variations n - n-1 : sma20-sma20n-1 sma50-sma50n-1 ...
			else:
				listToDB[43]="_"
	except IndexError:
			listToDB[43]="_" 

	rankdict={}
	# calcul du rank
	for i in range(11,42,5):
		if i>=26 : rankdict.update({ i+3 : listToDB[i] })
	rankdict_=dict(sorted(rankdict.items(), key=lambda item: float(item[1])))
	j=0
	for x in rankdict_:
		listToDB[x]=int(j)
		j+=1
			
	# breakout
	try:
		listToDB[40]=int(ultat[0][40])	
		# reprend l'ancien booléen / high / break out
		# si position cours=3 > mm longues et position n/n-1 est passée à 3 , on a passé les moyennes mobiles : 	
		if listToDB[44] == 3 and listToDB[44] > int(ultat[0][44]) and listToDB[52]=="_":    #position change et passe à 3
			listToDB[40]=1	                                        #booléen passe à 1, on cherche alors le high
			listToDB[52]="buildbreakout"
		if listToDB[40]==1 and listToDB[3]>ultat[0][3]:
			listToDB[30]=listToDB[3]	                            #valeur la plus haute
		if listToDB[40]==1 and listToDB[3]<ultat[0][3]:	            #nouvelle valeur moins haute, on redescend
			listToDB[40]=0	                                        #booléen passe à 0
	except IndexError:
			listToDB[40]=0
		#print("listToDB[40]",listToDB[40])

	boolhigh=0
	boolfee=0
	try:
		if ultat[0][63] is not None:			# prix d'achat
			listToDB[63]=float(ultat[0][63])
	except IndexError:
		listToDB[63]=0
	try:
		if ultat[0][99] is not None:	# booléen / a été acheté ou non
			listToDB[99]=float(ultat[0][99])
	except IndexError:
		listToDB[99]=0

	try:
																				# prix supérieur à prix d'achat + 3*frais d'achat
		if float(listToDB[3])>(float(listToDB[63])*(1+0.3*float(listToDB[46]))): 	# prix est bon et déjà un achat, on peut vendre
				boolfee=1
		if float(listToDB[8])<=float(ultat[0][8]):  							# le rsi40 a dépassé son plus haut 
				boolhigh=1
	except IndexError:
			print("IndexError")

	prevcot=0
	try:
		if ultat[0][3] is not None:
			prevcot=float(ultat[0][3])
		if ultat[0][59] is not None:
			listToDB[59]=ultat[0][59]
		else:
			listToDB[59]=timest
		if ultat[0][66] is not None:
			listToDB[66]=ultat[0][66]
		else:
			listToDB[66]="_"
	except IndexError:
			listToDB[59]=timest
			listToDB[66]="_"
	
	try:
		if ultat[0][13] is not None :
			listToDB[13]=float(ultat[0][13])
	except:
		listToDB[13]=0

	# prev total buy price
	try:
		if ultat[0][83] is not None:
			listToDB[83]=round(float(ultat[0][83]),6)
	except:
		listToDB[83]=0
	try:
		if ultat[0][45] is not None:
			listToDB[45]=round(float(ultat[0][45]),6)
	except:
		listToDB[45]=0
	
	moyenne = round(numpy.mean(lstat), 6)
	ecarttype = round(numpy.std(lstat), 6)
	fraistransaction = round(listToDB[3]*listToDB[46]*2, 6)	# frais par transaction
	
	listToDB[93] = round(ecarttype/moyenne*100, 6)	# mean / standard deviation

	strat=strategy.Strat(listSymbolMeanStd,listToDB[0],moyenne,ecarttype,listToDB[93])
	rank_=strat.getRank()
	listToDB[94] = rank_	# rank
	print(strat.liste)
	listToDB[95] = round((ecarttype - fraistransaction),6)	# diff
	
	pourlestests=1

	if listToDB[60]=="incrossup30m" and listToDB[99]==0 : #and pourlestests==0 :
		listToDB[64]="achat"
		listToDB[65]="incrossup30m"
		listToDB[35]="incrossup30m"
		print("2 incrossup30m")
		tpl=input(round(float(price),6),listToDB[46])	# listToDB[46] fee
		if isinstance(tpl, list):
			listToDB[13]=tpl[0]	# nombre de coins (tradetable !)
			listToDB[10]=tpl[1]	# portfolio (tradetable !)
			listToDB[83]=tpl[2]	# budget achat prevtotalbuyprice
			listToDB[79]=tpl[3]	# marge cumulée
			listToDB[45]=round(float(price),6)
			listToDB[99]=1
			insertTrade(listToDB)
			title=coin+"-"+str(timestamp)+"-"+listToDB[65]
			_thread.start_new_thread(sendlist,(ultat.copy(),listToDB.copy(),title))
		
	elif listToDB[62]=="incrossup15m" and listToDB[99]==0 : #and pourlestests==0:
		print("2 incrossup15m")
		listToDB[64]="achat"
		listToDB[65]="incrossup15m"
		listToDB[35]="incrossup15m"
		tpl=input(price,listToDB[46])
		if isinstance(tpl, list):
			listToDB[13]=tpl[0]	# nombre de coins (tradetable !)
			listToDB[10]=tpl[1]	# portfolio (tradetable !)
			listToDB[83]=tpl[2]	# budget achat prevtotalbuyprice
			listToDB[79]=tpl[3]	# marge cumulée
			listToDB[63]=listToDB[3]
			listToDB[45]=round(float(price),6)
			listToDB[99]=1
			insertTrade(listToDB)
			title=coin+"-"+str(timestamp)+"-"+listToDB[65]
			_thread.start_new_thread(sendlist,(ultat.copy(),listToDB.copy(),title))

		# variations de n/n-1 : listToDB[43] + ça monte, - ça descend
		# sma7 = 0 constant
        # listToDB[12] : le cours monte ou descend sma7 ? sma7 constant
		# signe variation cours and position
		# à réétudier
        # variation du signe and position (au-dessus mm longues) and le cours monte and cours>au plus haut
	elif  float(listToDB[3])>prevcot and  listToDB[44] == 3  and  float(listToDB[3]) >= float(listToDB[30]) and listToDB[40]==0 and listToDB[43] == "var_sign_up" and listToDB[12]<=0 and pourlestests==0 and listToDB[99]==0 : 
		listToDB[64]="achat"
		listToDB[65]="entree_breakout"		
		listToDB[35]="entree_breakout"
		tpl=input(price,listToDB[46])
		if isinstance(tpl, list):
			listToDB[13]=tpl[0]	# nombre de coins (tradetable !)
			listToDB[10]=tpl[1]	# portfolio (tradetable !)
			listToDB[83]=tpl[2]	# budget achat prevtotalbuyprice
			listToDB[79]=tpl[3]	# marge cumulée
			listToDB[63]=listToDB[3]
			listToDB[66]="waitrsi40xy"
			listToDB[45]=round(float(price),6)
			listToDB[52]="_"
			listToDB[99]=1
			insertTrade(listToDB)
			title=coin+"-"+str(timestamp)+"-"+listToDB[65]
			_thread.start_new_thread(sendlist,(ultat.copy(),listToDB.copy(),title))

	#if listToDB[8]>seuil and boolhigh==1 and listToDB[99]==1 : # and boolfee==1 :
			listToDB[64]="vente"
			listToDB[65]="outYhighX"
			if listToDB[63] > 0 and listToDB[83] > 0 :
				valuemargin=round((float(listToDB[3])-float(listToDB[63])),6)
				listToDB[24]=str(round((((float(listToDB[3])-float(listToDB[63]))/float(listToDB[63]))*100),2))+"%"
				tpl=output(price,listToDB[46],listToDB[13])
				listToDB[13]=tpl[0]	# nombre de coins (tradetable !)
				listToDB[10]=tpl[1]	# portfolio (tradetable !)
				listToDB[79]=tpl[2]	# marge cumulée
				listToDB[14]=valuemargin
				trademargin=round(float(listToDB[13])*valuemargin,6)
				marginsum=round(listToDB[79]+trademargin,6)
				listToDB[78]=trademargin
				listToDB[79]=marginsum
				listToDB[40]=0	# booleen
				listToDB[66]="_"
				listToDB[83]=0	# no more for sale
				listToDB[99]=0
				insertTrade(listToDB)
				title=coin+"-"+str(timestamp)+"-"+listToDB[65]
				_thread.start_new_thread(sendlist,(ultat.copy(),listToDB.copy(),title))

	elif listToDB[55]=="outcrossdown15" and listToDB[99]==1 : # and boolfee==1 :
			listToDB[64]="vente"
			listToDB[65]="outcrossdown15"
			if listToDB[63] > 0 and listToDB[83] > 0 :
				valuemargin=round((float(listToDB[3])-float(listToDB[63])),6)
				listToDB[24]=str(round((((float(listToDB[3])-float(listToDB[63]))/float(listToDB[63]))*100),2))+"%"
				tpl=output(price,listToDB[46],listToDB[13])
				listToDB[13]=tpl[0]	# nombre de coins (tradetable !)
				listToDB[10]=tpl[1]	# portfolio (tradetable !)
				listToDB[79]=tpl[2]	# marge cumulée
				listToDB[14]=valuemargin
				trademargin=round(float(listToDB[13])*valuemargin,6)
				marginsum=round(listToDB[79]+trademargin,6)
				listToDB[78]=trademargin
				listToDB[79]=marginsum
				listToDB[83]=0	# no more for sale
				listToDB[99]=0
				insertTrade(listToDB)
				title=coin+"-"+str(timestamp)+"-"+listToDB[65]
				_thread.start_new_thread(sendlist,(ultat.copy(),listToDB.copy(),title))

	elif listToDB[15]=="outcrossdown5" and listToDB[99]==1 : # and boolfee==1 :
			listToDB[64]="vente"
			listToDB[65]="outcrossdown5"
			if listToDB[63] > 0 and listToDB[83] > 0 :
				valuemargin=round((float(listToDB[3])-float(listToDB[63])),6)
				listToDB[24]=str(round((((float(listToDB[3])-float(listToDB[63]))/float(listToDB[63]))*100),2))+"%"
				tpl=output(price,listToDB[46],listToDB[13])
				listToDB[13]=tpl[0]	# nombre de coins (tradetable !)
				listToDB[10]=tpl[1]	# portfolio (tradetable !)
				listToDB[79]=tpl[2]	# marge cumulée
				listToDB[14]=valuemargin
				print("1 outcrossdown5, marge cumulée listToDB[79], valuemargin listToDB[14]",listToDB[79],listToDB[14])
				trademargin=round(float(listToDB[13])*valuemargin,6)
				marginsum=round(listToDB[79]+trademargin,6)
				listToDB[78]=trademargin
				listToDB[79]=marginsum
				print("2 outcrossdown5, marge cumulée listToDB[79] ",listToDB[79])
				listToDB[83]=0	# no more for sale
				listToDB[99]=0
				insertTrade(listToDB)
				title=coin+"-"+str(timestamp)+"-"+listToDB[65]
				_thread.start_new_thread(sendlist,(ultat.copy(),listToDB.copy(),title))
			
	#if float(listToDB[3])>(float(listToDB[63])*(1+5*float(listToDB[46]))):
			listToDB[64]="vente"
			listToDB[65]="__%__"
			if listToDB[63] > 0 and  listToDB[83] > 0 :
				valuemargin=round((float(listToDB[3])-float(listToDB[63])),6)
				listToDB[24]=str(round((((float(listToDB[3])-float(listToDB[63]))/float(listToDB[63]))*100),2))+"%"
				tpl=output(price,listToDB[46],listToDB[13])
				listToDB[13]=tpl[0]	# nombre de coins (tradetable !)
				listToDB[10]=tpl[1]	# portfolio (tradetable !)
				listToDB[79]=tpl[2]	# marge cumulée
				listToDB[14]=valuemargin
				trademargin=round(float(listToDB[13])*valuemargin,6)
				marginsum=round(listToDB[79]+trademargin,6)
				listToDB[78]=trademargin
				listToDB[79]=marginsum
				listToDB[83]=0	# no more for sale
				listToDB[99]=0
				insertTrade(listToDB)
				title=coin+"-"+str(timestamp)+"-"+listToDB[65]
				_thread.start_new_thread(sendlist,(ultat.copy(),listToDB.copy(),title))
			
	insertCoin(listToDB)
	_thread.exit()
	
# dump(list, file_object)
# write list to binary file
def sendlist(ultat,listToDB,title):
	listlevel2=[]
	listlevel2.append(tuple(listToDB))
	listlevel2+=ultat
	filpath="./uploaddir/"+title
	# store list in binary file so 'wb' mode
	with open(filpath, 'wb') as fp:
		pickle.dump(listlevel2, fp)
	filserverpath="domain.com/graphin/"+title
	with FTP(host, user, password) as ftp :
		with open(filpath, "rb") as f:
			ftp.storbinary("STOR " + filserverpath, f)

# Démarrer un nouveau thread pour l'interface WebSocket
_thread.start_new_thread(ws_thread, ())

while True:
	yves=1
