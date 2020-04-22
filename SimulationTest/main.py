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
import potion
import os
import json
import time
import random

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

            command = "nohup python -c 'import potion; potion.createBlockchain(" + nodes + ", " + malicious + ")' > /dev/null 2>&1 &"
            Popen([command], shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)

            print "\nCreating blockchain...\n"
    
            items = list(range(1, int(nodes)))
            l = len(items)
            for i, item in enumerate(items):
                while True:
                    if (os.popen("docker ps | grep -oP node" + str(i+1)).read()):
                        printProgressBar(i + 1, l + 1, prefix = 'Progress:', suffix = 'Complete...', length = 50)
                        break

            while True:
                if (os.popen("docker ps | grep -oP nodeMonitor4").read()):
                    printProgressBar(l + 1, l + 1, prefix = 'Progress:', suffix = 'Complete...', length = 50)
                    break

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

        if (sys.argv[1] == '-r'):
            t = open('database/bitcoin', 'r')
            nodes = int(t.read())
            t.close()
            nodesNew = nodes

            while True:
                print "\x1b[6;30;42m[log]\x1b[0m : Performing change... ",
                what = random.randint(0, 1)
                if not (what):
                    change = str(random.randint(1, nodes))
                    address = os.popen("docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' node" + str(change)).read()
                    try:
                        os.system("docker kill node" + str(change))
                        os.system("docker rm node" + str(change))
                    except:
                        pass

                    time.sleep(int(sys.argv[2]))
                    print "Killed node" + str(change) + " with IP " + address,

                else:
                    what = random.randint(0, int(sys.argv[3]))
                    nodesNew += 1
                    os.system("docker run -it -d --name node" + str(nodesNew) + " ubuntu /bin/bash")
                    os.system("docker cp ../btcbin node" + str(nodesNew) + ":/")
                    if (what): os.system("docker exec -t node" + str(nodesNew) + " /btcbin/bitcoind -malicious -regtest -debug=net -daemon")
                    else: os.system("docker exec -t node" + str(nodesNew) + " /btcbin/bitcoind -regtest -debug=net -daemon")
                    time.sleep(int(sys.argv[2]))
                    if (what): os.system('docker exec -t node' + str(nodesNew) + ' /btcbin/bitcoin-cli -malicious -regtest addnode "172.17.0.' + str(random.randint(2, int(nodes)+1)) + ':18444" "onetry"')
                    else: os.system('docker exec -t node' + str(nodesNew) + ' /btcbin/bitcoin-cli -regtest addnode "172.17.0.' + str(random.randint(2, int(nodes)+1)) + ':18444" "onetry"')
                    address = os.popen("docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' node" + str(nodesNew)).read()
                    os.system('docker exec -t nodeMonitor /btcbin/bitcoin-cli -regtest addnode "' + address + ':18444" "onetry"')
                    os.system('docker exec -t nodeMonitor2 /btcbin/bitcoin-cli -regtest addnode "' + address + ':18444" "onetry"')
                    os.system('docker exec -t nodeMonitor3 /btcbin/bitcoin-cli -regtest addnode "' + address + ':18444" "onetry"')
                    os.system('docker exec -t nodeMonitor4 /btcbin/bitcoin-cli -regtest addnode "' + address + ':18444" "onetry"')
                    t = open('database/bitcoin', 'w')
                    t.write(str(nodesNew))
                    t.close()
                    if (what): print "Creating malicious node" + str(nodesNew) + " with IP " + address,
                    else: print "Creating node" + str(nodesNew) + " with IP " + address,

                potionOutput = ""

        if (sys.argv[1] == '-t'):
            addressMonitor = os.popen("docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' nodeMonitor").read()
            addressMonitor2 = os.popen("docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' nodeMonitor2").read()
            addressMonitor3 = os.popen("docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' nodeMonitor3").read()
            addressMonitor4 = os.popen("docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' nodeMonitor4").read()
            f = open("database/results", "w")
            f2 = open("database/results2", "w")
            f3 = open("database/results3", "w")
            f4 = open("database/results4", "w")

            p = open("database/potionout", "w")
            c = open("database/nodes", "w")
            f.write("[<Test>] <correct_connections> | <missing_connections> | <poc_verified_connections> :\n")
            f2.write("[<Test>] <correct_connections> | <missing_connections> | <poc_verified_connections> :\n")
            f3.write("[<Test>] <correct_connections> | <missing_connections> | <poc_verified_connections> :\n")
            f4.write("[<Test>] <correct_connections> | <missing_connections> | <poc_verified_connections> :\n")

            for i in range(0,int(sys.argv[2])):
                t = open('database/bitcoin', 'r')
                nodes = int(t.read())
                t.close()

                print "\x1b[6;30;42m[log]\x1b[0m : Performing test " + str(i) + "..."
                potionOutput = ""
                potionOutput2 = ""
                potionOutput3 = ""
                potionOutput4 = ""

                try:
                    info = os.popen("docker exec -t nodeMonitor /btcbin/bitcoin-cli -regtest getnetnodesinfo").read()
                    data = json.loads(info)
                    for a in range(0,nodes-1):
                        for b in range(0,nodes-1):
                            try:
                                if not (data[a]["peers"][b]["inbound"]):
                                    potionOutput = potionOutput + data[a]["peers"][b]["addr"] + "\n"
                            except:
                                pass
                    info = os.popen("docker exec -t nodeMonitor2 /btcbin/bitcoin-cli -regtest getnetnodesinfo").read()
                    data = json.loads(info)
                    for a in range(0,nodes-1):
                        for b in range(0,nodes-1):
                            try:
                                if not (data[a]["peers"][b]["inbound"]):
                                    potionOutput2 = potionOutput2 + data[a]["peers"][b]["addr"] + "\n"
                            except:
                                pass
                    info = os.popen("docker exec -t nodeMonitor3 /btcbin/bitcoin-cli -regtest getnetnodesinfo").read()
                    data = json.loads(info)
                    for a in range(0,nodes-1):
                        for b in range(0,nodes-1):
                            try:
                                if not (data[a]["peers"][b]["inbound"]):
                                    potionOutput3 = potionOutput3 + data[a]["peers"][b]["addr"] + "\n"
                            except:
                                pass

                    info = os.popen("docker exec -t nodeMonitor4 /btcbin/bitcoin-cli -regtest getnetnodesinfo").read()
                    data = json.loads(info)
                    for a in range(0,nodes-1):
                        for b in range(0,nodes-1):
                            try:
                                if not (data[a]["peers"][b]["inbound"]):
                                    potionOutput4 = potionOutput4 + data[a]["peers"][b]["addr"] + "\n"
                            except:
                                pass
                except:
                    pass

                correct = 0
                missing = 0
                correct2 = 0
                missing2 = 0
                correct3 = 0
                missing3 = 0
                correct4 = 0
                missing4 = 0

                for x in range(1,nodes+1):
                    try:
                        info = os.popen("docker exec -t node" + str(x) + " /btcbin/bitcoin-cli -regtest getpeerinfo").read()
                        data = json.loads(info)
                        a = 0
                        a2 = 0
                        a3 = 0
                        a4 = 0

                        while True:
                            try:
                                if not (data[a]["inbound"]) and (addressMonitor[:len(addressMonitor)-1] not in data[a]["addr"]):
                                    c.write(data[a]["addr"] + "\n")
                                    if (data[a]["addr"] in potionOutput): correct += 1
                                    else: 
                                        missing += 1
                                        print "\x1b[6;30;42m[log]\x1b[0m : New missing connection --->" + data[a]["addr"]
                                a+=1
                            except:
                                break
                        while True:
                            try:
                                if not (data[a2]["inbound"]) and (addressMonitor2[:len(addressMonitor2)-1] not in data[a2]["addr"]):
                                    c.write(data[a2]["addr"] + "\n")
                                    if (data[a2]["addr"] in potionOutput2): correct2 += 1
                                    else: 
                                        missing2 += 1
                                        print "\x1b[6;30;42m[log]\x1b[0m : New missing connection --->" + data[a2]["addr"]
                                a2+=1
                            except:
                                break
                        while True:
                            try:
                                if not (data[a3]["inbound"]) and (addressMonitor3[:len(addressMonitor3)-1] not in data[a3]["addr"]):
                                    c.write(data[a3]["addr"] + "\n")
                                    if (data[a3]["addr"] in potionOutput3): correct3 += 1
                                    else: 
                                        missing3 += 1
                                        print "\x1b[6;30;42m[log]\x1b[0m : New missing connection --->" + data[a3]["addr"]
                                a3+=1
                            except:
                                break
                        while True:
                            try:
                                if not (data[a4]["inbound"]) and (addressMonitor4[:len(addressMonitor4)-1] not in data[a4]["addr"]):
                                    c.write(data[a4]["addr"] + "\n")
                                    if (data[a4]["addr"] in potionOutput4): correct4 += 1
                                    else: 
                                        missing4 += 1
                                        print "\x1b[6;30;42m[log]\x1b[0m : New missing connection --->" + data[a4]["addr"]
                                a4+=1
                            except:
                                break                                                                
                    except:
                        pass

                res = "[" + str(i) + "] " + str(correct) + " | " + str(missing) + " | " + str(potionOutput.count('\n'))
                f.write(res + "\n")
                res = "[" + str(i) + "] " + str(correct2) + " | " + str(missing2) + " | " + str(potionOutput2.count('\n'))
                f2.write(res + "\n")
                res = "[" + str(i) + "] " + str(correct3) + " | " + str(missing3) + " | " + str(potionOutput3.count('\n'))
                f3.write(res + "\n")
                res = "[" + str(i) + "] " + str(correct4) + " | " + str(missing4) + " | " + str(potionOutput4.count('\n'))
                f4.write(res + "\n")

                print "\x1b[6;30;42m[log]\x1b[0m : Test result ---> " + res
                p.write(potionOutput + "\n\n")
                c.write("\n")
                time.sleep(int(sys.argv[3]))

            f.close()
            f2.close()
            f3.close()
            f4.close()
            p.close()


def printProgressBar(iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)

    sys.stdout.write('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix))
    sys.stdout.flush()

    if iteration == total:
        print " Done!\n"

main()