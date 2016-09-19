#!/bin/python
import os,re
import time
import subprocess
import threading
import Queue
#from myGlobal import myGlobal
from threading import *
from argparse import ArgumentParser
from netaddr import IPNetwork, IPAddress

parser = ArgumentParser(description="dynamic qdisc change test")
parser.add_argument('--intf',
                    dest="intf",
                    type=str,
                    action="store",
                    help="list of intf to be monitored")
parser.add_argument('--iter',
                    dest="iter",
                    type=int,
                    action="store",
                    help="number of iterations")
parser.add_argument('--ipblock',
                    dest="ipblock",
                    type=str,
                    action="store",
                    help="ipblocks of low delay traffic")
parser.add_argument('--cToS',
                    dest="cToS",
                    type=bool,
                    action="store",
                    help="whether it is a clientToServer communication(e.g.Iperf)")
parser.add_argument('--portRange',
                    dest="portRange",
                    type=str,
                    action="store",
                    help="low delay traffic portRange from min to max (e.g.300-3000)")
parser.add_argument('--linkCap',
                    dest="linkCap",
                    type=str,
                    action="store",
                    help="linkCap of the interested link. This field is used to set tc max rate")
args = parser.parse_args()
prev_flows = {}
def flowsMetaData(flows, outPort):
    nLowDelay = 0.0
    nNonLow = 0.0
    for flow in flows:
	if (outPort == flow['outPort']):
		if(flow['lowDelay']): 
			nLowDelay = nLowDelay + 1
		else:
			nNonLow = nNonLow + 1
    #print nLowDelay, nNonLow
    if (nLowDelay+nNonLow!=0):
    	ratio = nLowDelay/(nLowDelay+nNonLow)
    else : 
	ratio = 0.0
    return ratio, nLowDelay, nNonLow 

def changeQdisc(linkCap, ratio, intfs):
	rate1 = 0.02
	print "haha ratio "+str(ratio)
	if ratio < 0.2 :
		rate1 = linkCap*0.2
	elif ratio > 0.9 :
		rate1 = linkCap*0.9
	else: 
		rate1 = linkCap*ratio
	rate2 = linkCap - rate1
	#print ratio
	print ("now the min rate for low delay queue is %s", rate1)
	print ("now the min rate for data queue is %s", rate2)
	cmd = 'bash tc_change_diff2.sh %s %s %s ' % (linkCap,rate1,rate2)
	#print intfs
	for intf in intfs.keys():
		cmd = cmd + intf +" "
	print cmd
	os.system(cmd)

def findPortMinMax(portRange):
	portMinMax = portRange.split('-')
	portMin = 0
	portMax = 0
	if len(portMinMax) == 2:
		portMin = int(portMinMax[0])
		portMax = int(portMinMax[1])+1
	else :
		portMin = int(portMinMax[0])
		portMax = int(portMinMax[0])+1
	#print portMin,portMax
	return range(portMin, portMax)
def detectflows(intf, servIP, portRange, cToS):
    flows = []
    tccmd = "sudo ovs-ofctl dump-flows "+intf
    result = subprocess.check_output(tccmd,shell=True)
    portTrueRange = findPortMinMax(portRange)
    for item in result.split('\n'):
	elem = item.split(',')
	if len(elem)<=9:
		pass
	elif elem[9]=='tcp':
	   #print '---------flows--------'
	   #print item

	   if (cToS):
		servPort = elem[-1].split(' ')[0].split('=')[1]
		if IPAddress(elem[-4].split('=')[1]) in IPNetwork(servIP) and int(servPort) in portTrueRange:
				flow = {'serverIP':elem[-4].split('=')[1], 'serverPort':servPort, 'clientIP':elem[-5].split('=')[1], 'clientPort':elem[-2].split('=')[1], 'durations':elem[1].split('=')[1], 'packets':elem[3].split('=')[1], 'bytes':elem[4].split('=')[1], 'outPort':elem[-1].split(' ')[1].split(':')[1],'lowDelay':True}
				flows.append(flow)
			
		else :
				flow = {'serverIP':elem[-4].split('=')[1], 'serverPort':servPort, 'clientIP':elem[-5].split('=')[1], 'clientPort':elem[-2].split('=')[1], 'durations':elem[1].split('=')[1], 'packets':elem[3].split('=')[1], 'bytes':elem[4].split('=')[1], 'outPort':elem[-1].split(' ')[1].split(':')[1],'lowDelay':False}
				flows.append(flow)
						
	   else:
		servPort = elem[-2].split('=')[1]
		if IPAddress(elem[-5].split('=')[1]) in IPNetwork(servIP) and int(servPort) in portTrueRange:
				flow = {'serverIP':elem[-5].split('=')[1], 'serverPort':servPort, 'clientIP':elem[-4].split('=')[1], 'clientPort':elem[-1].split(' ')[0].split('=')[1], 'durations':elem[1].split('=')[1], 'packets':elem[3].split('=')[1], 'bytes':elem[4].split('=')[1], 'outPort':elem[-1].split(' ')[1].split(':')[1],'lowDelay':True}
				flows.append(flow)
		else :	     
				flow = {'serverIP':elem[-5].split('=')[1], 'serverPort':servPort, 'clientIP':elem[-4].split('=')[1], 'clientPort':elem[-1].split(' ')[0].split('=')[1], 'durations':elem[1].split('=')[1], 'packets':elem[3].split('=')[1], 'bytes':elem[4].split('=')[1],'outPort':elem[-1].split(' ')[1].split(':')[1], 'lowDelay':False}
				flows.append(flow)
		
#	print "----------------"
    
    #parse_result = re.compile(r'qdisc\s*[a-zA-Z_]+\s+([0-9]+):\sdev\s([a-zA-Z0-9-]+)\sroot\s[a-zA-Z0-9_.:\s]+Sent\s([\d]+)\sbytes\s([\d]+)\spkt\s\(dropped\s([\d]+),\soverlimits\s([\d]+)\srequeues\s([\d]$
    #matches_d = parse_result.findall(result)
    return flows

############################
# This is a simple function for extracting useful info from tc -s qdisc show
# entries[]:
# Extracted columns include:
# 0 1 2 3 4 5 6 7 8 9
# idx RootNo. DevName Sent(Bytes) Sent(Packets) Dropped(Packets) Overlimits(Bytes) Requeues Backlog(Bytes) Backlog(Packets)
#
# Because linux tc may also show the child queue class, Parent, Queue Depth and Propagation Delay may also be considered
#
# RootNo is related to multiple Queues of an interface pls ignore at the current stage
#
############################
#Length of the stats collector moving window: maximaly holding 100 entries
MAX_BUF = 100

#This is the dict that holds all entries
tc_dict ={}

#Dictionary possible keys
entry_keys = ['RootNo','Dev','SentB','SentP','DroppedP','OverlimitsB','Requeues','BackB','BackP']

#Child queue possible keys
netem_keys = ['RootNo','Dev','Parent','Q_Depth','P_Delay','SentB','SentP','DroppedP','OverlimitsB','Requeues','BackB','BackP']

#Available interfaces (devices), e.g. eth1, eth0
#dev_keys = []

#Available child interfaces (devices)
#netem_dev_keys = []
#Time tracker
prev_t = 0
#idx = 0
def tcshow (intflist):
    '''
    This function handles a pulling event received from the timer
    It wakes up every 50ms (sampling time),collect all the data of all interfaces
    and store them in tc_dict
    '''
    # wait until being waken up
#    e.wait()
#    e.clear()
    
    # grab the locker and idx
#    tclock = myGlobal.tclock
#    idx = myGlobal.idx
#    global idx
    # calculate delta_t
    global prev_t
#    entry = []
    curr_t =time.time()
    delta_t = curr_t-prev_t
    prev_t = curr_t
    print "---------curr_t: %s -------------" % curr_t
    #Available interfaces (devices), e.g. eth1, eth0
#    dev_keys = []
    #Available child interfaces (devices)
#    netem_dev_keys = []
    
    #parse tc show root result
    tccmd = "tc -s qdisc show"
    #result = subprocess.check_output(tccmd,shell=True)
    #parse_result = re.compile(r'qdisc\s*[a-zA-Z_]+\s+([0-9]+):\sdev\s([a-zA-Z0-9-]+)\sroot\s[a-zA-Z0-9_.:\s]+Sent\s([\d]+)\sbytes\s([\d]+)\spkt\s\(dropped\s([\d]+),\soverlimits\s([\d]+)\srequeues\s([\d]+)\)\s*backlog\s([\d]+)b+\s([\d]+)p')
    #matches_d = parse_result.findall(result)
    #entry = [dict(zip(entry_keys,row)) for row in matches_d]
    #parse tc show parent result
    result2 = subprocess.check_output(tccmd,shell=True)
#    print result2
    parse_result2 = re.compile(r'qdisc\snetem\s+([0-9]+):\sdev\s([a-zA-Z0-9-]+)\sparent\s([0-9]+:[0-9]+)\slimit\s([0-9]+)\sdelay\s([0-9.]+)[mu]s[a-zA-Z0-9_.:\s]+Sent\s([\d]+)\sbytes\s([\d]+)\spkt\s\(dropped\s([\d]+),\soverlimits\s([\d]+)\srequeues\s([\d]+)\)\s*backlog\s([\dA-Z]+)b\s([\d]+)p')
    matches_d2 = parse_result2.findall(result2)
    netem_entry = [dict(zip(netem_keys,row)) for row in matches_d2]
    print matches_d2
    for i in range(0,len(matches_d2),2):
	for intf, values in intflist.items():
		if intf==matches_d2[i][1]:
#			print intf 
    			with open(intf+'.txt', 'a') as the_file:
				the_file.write("%s, %s, %s, %s, %s, %s, %s, %s\n" % (curr_t, delta_t, matches_d2[i][5],matches_d2[i+1][5],matches_d2[i][-1],matches_d2[i+1][-1],values['nVideo'],values['nData']))
#    with open('s0eth2.txt', 'a') as the_file2:
#	the_file2.write("%s, %s, %s, %s, %s, %s\n" % (curr_t, delta_t, matches_d2[2][5],matches_d2[3][5],matches_d2[2][-1],matches_d2[3][-1]))
    #print 
    #print netem_entry
    #save everything into a tc_dict{idx:{dev1:{'RootNo':...},dev2:{'RootNo':...}}}
    #for item in entry:
    	#print item
    #    for netem_item in netem_entry:
	#    if netem_item['Dev']==item['Dev']:
		#item.update({'P_Delay':netem_item['P_Delay']})
                #t = netem_item['BackB']
                #if t.endswith('K'):
		 # t = t[0:len(t)-1] + "000"
		#if t.endswith('M'):
                 # t = t[0:len(t)-1] + "000000"
		#item.update({'BackB':t}) 
        #item.update({'delta_t': delta_t})
        #dev_keys.append(item['Dev']) 
    #lock tc_dict and update it
    #tclock.acquire()
    #tc_dict.update({idx : dict(zip(dev_keys,entry))})
    #print tc_dict[idx]
    #if len(tc_dict) > MAX_BUF:
	#remove the out of boundary entry
        #del tc_dict[idx-MAX_BUF]
    #idx +=1
    #myGlobal.idx=idx
    #tclock.release()



class TControl(threading.Thread):
	'''
	A simple thread for controlling tcshow.
	This function is triggered by timer event
	'''
	def __init__(self,e,counter,intflist):
		super(TControl, self).__init__()
		self.keeprunning = counter
		self.intflist=intflist
		self.initial = counter
		self.event = e
		self.qchangecounter = 1
	def run(self):
		try:
			while self.keeprunning > 0:
				self.keeprunning-=1
				time.sleep(0.01)
				self.qchangecounter = self.qchangecounter + 1
				if self.qchangecounter > 10:
					applyQdiscMgmt(args.intf,args.ipblock,args.portRange,args.cToS)
					self.qchangecounter = 1

		except KeyboardInterrupt:
			print "stoptimer"
			self.stop()
	def stop(self):			
		self.keeprunning = 0
	def reset(self):
		self.keeprunning = self.initial
		sleep = False

def extractSwitchID(intf):
	switches = {}
	intfs = intf.split(',')
	intfs_dict = {}
	for item in intfs:
		#print item		
		port_dict = {}
		item_str = item.split('-')
		sw = item_str[0]
		port_dict['port']=item_str[1].split('eth')[1]
		intfs_dict[item]= port_dict
		if sw not in switches.keys():
			switches.setdefault(sw,[]).append(intfs_dict)
		else:
#			print intfs_dict
			if intfs_dict not in switches[sw]:
				switches.setdefault(sw,[]).append(intfs_dict)
		
		#print switches
		#intfsPerSwitch.append(item)
		#if sw not in switches.key():
	return switches

def applyQdiscMgmt(intf, ipblock, portRange, cToS):
	global prev_flows
	switches = extractSwitchID(intf)
	for sw in switches.keys():
		flowList = []
		flows = detectflows(sw, ipblock, portRange, cToS)
		for flow in flows:
			if flow['outPort'] =='2':
				flowList.append([flow['serverIP'],flow['serverPort'],flow['clientIP'],flow['clientPort'],flow['lowDelay'],flow['outPort']])
		for key, value in switches[sw][0].items():#for each port of a switch
			ratio, a,b = flowsMetaData(flows,value['port'])
			print value['port']+':'
			print ratio, a, b
			value['nVideo']=a
			value['nData']=b
			print value	
			switches[sw][0][key] = value					
		#print switches[sw][0]			
		print flowList
		
		if sw in prev_flows.keys():
			if prev_flows[sw] == flowList:
				print "flows did not change since last time"
			else:
				if flows:
					#print '-----flows-----'
					#print flows
					#print sw
					#print switches[sw] 
					ratio,nLow,nData = flowsMetaData(flows, '2')
					changeQdisc(float(args.linkCap), ratio, switches[sw][0])
					print "flows have been changed"
		prev_flows[sw] = flowList	
		tcshow(switches[sw][0])


if __name__ == '__main__':
	print args.iter
	print args.intf
	print args.ipblock
	e = threading.Event()
	counter = args.iter
	t1 = TControl(e,counter,args.intf.split(','))
	#t1.daemon = True
	#print flows
	#ratio = flowsMetaData(flows, '2')
	#changeQdisc(float(args.linkCap), ratio)
	t1.start()
