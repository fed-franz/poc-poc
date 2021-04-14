# -*- coding: utf-8 -*-

#################################################
#                                               #
# ATOM: proof of connection                     #
#                                               #
# Authors:                                      #
# Vanesa Daza - vanesa.daza@upf.edu             #
# Federico Franzoni - federico.franzoni@upf.edu #
# Xavier Salleras - xavier.salleras@upf.edu     #
#                                               #
#################################################

import sys
from subprocess import Popen
import multiprocessing
import potion
import os
import json
import time
import random
from random import choice
# from filelock import FileLock
from lockfile import LockFile


# mutex = multiprocessing.Lock()

def getNodeList(name="node", exclude="Monitor"):
    nodes = os.popen("docker ps --filter=\"name="+name+"\" --format '{{.Names}}'").readlines()
    nodeList = []
    for i in range(len(nodes)):
        n = nodes[i].rstrip()
        if exclude not in n:
            nodeList.append(n)

    return nodeList

def getRandList(num, name="node", exclude="Monitor"):
    randList = getNodeList(name, exclude)
    
    #shuffle
    random.shuffle(randList)
    #get first num elements
    del randList[num:]

    return randList

def getRandNode(name="node", exclude="Monitor"):
    rList = getRandList(1, name, exclude)
    if(len(rList)>0):
        return rList[0]

def IP(str):
    return str.split(':')[0]

def getNodeIP(node):
    ip = os.popen("docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "+node).read().rstrip()

    if ip == "127.0.0.1":
        print "ERR 127.0.0.1 "+node

    return ip

def findNode(addr):
    # print "findNode "+addr
    nodeList = getNodeList()
    for node in nodeList:
        nodeAddr = getNodeIP(node)
        # print node+":"+nodeAddr
        if nodeAddr == addr:
            return node

def getNewNodeName():
    nodeList = getNodeList()
    
    num=1
    while "node"+str(num) in nodeList:
        num += 1

    return "node"+str(num)

def getPeers(node,bound="all"):
    # bool inbound=False
    if bound=="inbound": inbound=True
    else: inbound=False

    peerList=[]
    try:
        info = os.popen("docker exec -t " + node + " /btcbin/bitcoin-cli -regtest getpeerinfo").read()
        data = json.loads(info)
        for peer in range(0,len(data)):
            if bound!="all":
                if (data[peer]["inbound"] != inbound):
                    continue

            P_N = IP(data[peer]["addr"])
            pNode = findNode(P_N)
            if pNode != None: # 
                peerList.append(pNode)
    except:
        pass

    return peerList

#################################################
# mutex = threading.Lock()

def changeNet():
    lock = LockFile("lock.x")
    adds=0
    rms=0
    while True:
        with lock:
            nodeList = getNodeList()
            numNodes = len(nodeList)
            numMals = 0
            for node in nodeList:
                ismal = os.popen("docker exec -t "+node+" ps -x | grep malicious").read()
                if 'malicious' in ismal :
                    numMals += 1

            print ""
            print "Num nodes:"+str(numNodes)+" (malicious: "+str(numMals)+")"
            print "\x1b[6;30;42m[log]\x1b[0m : Performing change... ",
            # TODO do options: new/rm node + new/rm conn
            # if(numNodes<8): what=1
            # else: 
            if abs(rms-adds) > 3:
                if adds>rms: what=True
                else: what=False
            else:
                what = random.randint(0, 1)
            if not (what):
                rms+=1

                # Stop node
                rmNode = getRandNode()
                print "RM "+rmNode

                #Open new outbound connection for disconnected peers
                inpeers = getPeers(rmNode,"inbound")
                for node in inpeers:
                    nodepeers = getPeers(node)
                    pto = choice([r for r in nodeList if r not in nodepeers ])
                    print node+"-->"+pto
                    os.system('docker exec -t ' + node + ' /btcbin/bitcoin-cli -regtest addnode "' + getNodeIP(pto) + ':18444" "onetry"')
                    nodepeers.append(pto)

                os.system("docker exec -t " + rmNode + " /btcbin/bitcoin-cli -regtest stop > /dev/null")
                time.sleep(0.3)
                os.system("docker kill " + rmNode+">/dev/null")
                os.system("docker rm " + rmNode+">/dev/null")

            else:
                adds+=1

                malRatio = (numMals * 100 / numNodes)                    
                probMalicious = int(sys.argv[3])
                if (malRatio < probMalicious):
                    print "Mal RATIO: "+str(malRatio)
                    what = True
                else:
                    what = False
                
                newNode = getNewNodeName()
                os.system("docker run -it -d --name " + newNode + " ubuntu /bin/bash > /dev/null")
                os.system("docker cp ../btcbin " + newNode + ":/")
                # Run malicious node
                if (what): 
                    os.system("docker exec -t " + newNode + " /btcbin/bitcoind -malicious -regtest -debug=net -daemon > /dev/null")
                # Run node
                else: 
                    os.system("docker exec -t " + newNode + " /btcbin/bitcoind -regtest -debug=net -daemon > /dev/null")
                time.sleep(1)

                # Connect monitors
                address = getNodeIP(newNode)
                os.system('docker exec -t nodeMonitor /btcbin/bitcoin-cli -regtest addnode "' + address + ':18444" "onetry"')
                os.system('docker exec -t nodeMonitor2 /btcbin/bitcoin-cli -regtest addnode "' + address + ':18444" "onetry"')
                os.system('docker exec -t nodeMonitor3 /btcbin/bitcoin-cli -regtest addnode "' + address + ':18444" "onetry"')
                os.system('docker exec -t nodeMonitor4 /btcbin/bitcoin-cli -regtest addnode "' + address + ':18444" "onetry"')
                
                if (what): print "NEW malicious " + newNode + " with IP " + address + "\n",
                else: print "NEW " + newNode + " with IP " + address + "\n",

                num_conns = 3
                newpeers = []
                # for i in range(0, num_conns):
                outconns = 0
                while outconns < 3:    
                    try:
                        pto = choice([r for r in nodeList if r not in newpeers ])
                        print newNode+"-->"+pto
                        os.system('docker exec -t ' + newNode + ' /btcbin/bitcoin-cli -regtest addnode "' + getNodeIP(pto) + ':18444" "onetry"')
                        newpeers.append(pto)
                        outconns += 1
                    except:
                        pass
    
                # Add inbound connections
                inconns = 0
                while inconns < 2:
                    try:
                        pfrom = choice([r for r in nodeList if r not in newpeers ])
                        print pfrom+"-->"+newNode
                        os.system('docker exec -t ' + pfrom + ' /btcbin/bitcoin-cli -regtest addnode "' + address + ':18444" "onetry"')
                        newpeers.append(pfrom)
                        inconns += 1
                    except:
                        pass
                
        time.sleep(int(sys.argv[2]))
#####

def testAToM():
    addressMonitor = getNodeIP("nodeMonitor")
    f = open("database/results", "w")
    f.write("[<Test>] <true_connections> | <correct_connections> | <missing_connections> | <fake_connections> :\n")
    print "[<\#>] <G> | <TP> | <FN> | <FP> :\n"

    lock = LockFile("lock.x")
    for i in range(0,int(sys.argv[2])):        
        with lock:
            # Retrieve topology
            G = {}
            # for each running node
            nodeList = getNodeList()
            for n in nodeList:
                # if not n:
                #     break
                # try:
                    # retrieve peers
                    try:
                        info = os.popen("docker exec -t " + n + " /btcbin/bitcoin-cli -regtest getpeerinfo").read()
                        data = json.loads(info)
                    except:
                        print "ERROR: "+info
                        # print "127.0.0.1: "+n

                    N = getNodeIP(n)
                    G[N] = []
                    for peer in range(0,len(data)):
                        if not (data[peer]["inbound"]):
                            P_N = IP(data[peer]["addr"])
                            G[N].append(P_N)

                    # print "G_N"
                    # print G[N]
                                                    
                # except:                    
                #     pass

            # print "G"
            # print G

            # Retrieve topology snapshot
            G_ATOM = {}
            G_M = {}
            # try:
            info = os.popen("docker exec -t nodeMonitor /btcbin/bitcoin-cli -regtest getnetnodesinfo").read()
            data = json.loads(info)
            
            for node in range(0,len(data)):
                N = IP(data[node]["node"])
                G_M[N] = [] 
                
                for peer in range(0,len(data[node]["peers"])):
                    # print data[node]["peers"][peer]
                    P = IP(data[node]["peers"][peer]["addr"])
                    if not (data[node]["peers"][peer]["inbound"]):
                        # print "OUT: " + P
                        G_M[N].append(P)
                    # else:
                    #     print "IN: " + P
                    
            # except:
            #     print "!"
            #     pass
            # print G_M
            G_ATOM = G_M #TODO: set to majority
        
            # Calculate accuracy
            tot=0
            correct=0
            miss=0
            fake=0
            for n in G:
                if n not in G_ATOM:
                    print "ERR: node mismatch"
                    continue

                for p in G[n]:
                    tot += 1
                    if p in G_ATOM[n]:
                        correct += 1
                        # print "OK"
                    else:
                        miss +=1
                        # print "MISS"

            # Verify G_ATOM does not have fake links
            for n in G_ATOM:
                if n not in G:
                    print "ERR: node mismatch"
                    continue

                for p in G_ATOM[n]:
                # f.write("[<Test>] <true_connections> | <correct_connections> | <missing_connections> | <fake_connections> :\n")
                    if p not in G[n]:
                        fake += 1
                        print "FAKE:"+n+"->"+p

            res = "[" + str(i) + "] " + str(tot) + " | " + str(correct) + " | " + str(miss) + " | " + str(fake)
            print res
            f.write(res + "\n")
        time.sleep(int(sys.argv[3]))
    #endfor (Tests)

    f.close()
            
#####

#_____ MAIN _____#
def main():
    if (len(sys.argv) < 2):
        print "\nUSAGE:\n"
        print "sudo python main.py [OPTION] [arg]\n"
        print "Where [OPTION] means:"
        print "-s : Create a bitcoin blockchain of [arg] trusty nodes plus [arg2] malicious nodes."
        print "-d : Delete bitcoin blockchain."
        print "-t : Run [arg] tests and get results awaiting [arg2] seconds between tests."
        print "-r : Randomise the network awaiting [arg] seconds between each change and [arg2] ratio of malicious."
        print ""

    else:
        if (sys.argv[1] == '-s'):
            nodes = sys.argv[2]
            malicious = sys.argv[3]
            totalNodes = int(nodes) + int(malicious)
            os.system("mkdir database")
            f = open('database/bitcoin', 'w')
            f.write(str(totalNodes))
            f.close()

            potion.createBlockchain(nodes,malicious)

        if (sys.argv[1] == '-d'):
            f = open('database/bitcoin', 'r')
            nodes = f.read()
            command = "nohup python -c 'import potion; potion.deleteBlockchain(" + nodes + ", \"s\")' > /dev/null 2>&1 &"
            Popen([command], shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)
            f.close()

            print "\nDestroying blockchain...\n"
    
            items = list(range(1, int(nodes)))
            l = len(items)
            for i, item in enumerate(items):
                while True:
                    if not (os.popen("docker ps | grep -oP node" + str(i+1)).read()):
                        printProgressBar(i + 1, l + 1, prefix = 'Progress:', suffix = 'Complete...', length = 50)
                        break

            while True:
                if not (os.popen("docker ps | grep -oP nodeMonitor4").read()):
                    printProgressBar(l + 1, l + 1, prefix = 'Progress:', suffix = 'Complete...', length = 50)
                    break


        # Create lock file
        lockfile=open("lock.x","w")
        lockfile.close()

        ### CHANGE NETWORK ###
        if (sys.argv[1] == '-r'):
            # multiprocessing.Process(target=changeNet, arg=(mutex)).start() 
            changeNet()
            # args=sys.argv

        ### TEST ATOM ###
        if (sys.argv[1] == '-t'):
            # multiprocessing.Process(target=testAToM).start()
            testAToM()
            # t = threading.Thread(target = testAToM)
            # t.start()
            # t.join()


def printProgressBar(iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)

    sys.stdout.write('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix))
    sys.stdout.flush()

    if iteration == total:
        print " Done!\n"

main()
