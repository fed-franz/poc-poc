# -*- coding: utf-8 -*-

#################################################
#                                               #
# PoTION: Proof of connecTION                   #
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

def main():
    if (len(sys.argv) < 2):
        print "\nUSAGE:\n"
        print "sudo python main.py [OPTION] [arg]\n"
        print "Where 'a' means:"
        print "-s : Create and populate a bitcoin blockchain of [arg] nodes."
        print "-d : Delete bitcoin blockchain."
        print "-b : Get balances of the nodes."
        print "-a : Retrieve addresses of nodes."
        print ""

    else:
        if (sys.argv[1] == '-s'):
            nodes = sys.argv[2]
            os.system("mkdir database")
            f = open('database/bitcoin', 'w')
            f.write(nodes)
            f.close()

            command = "nohup python -c 'import potion; potion.createBlockchain(" + nodes + ")' > /dev/null 2>&1 &"
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
                if (os.popen("docker ps | grep -oP nodeMonitor").read()):
                    printProgressBar(l + 1, l + 1, prefix = 'Progress:', suffix = 'Complete...', length = 50)
                    break

        if (sys.argv[1] == '-d'):
            f = open('database/bitcoin', 'r')
            command = "nohup python -c 'import potion; potion.deleteBlockchain(" + f.read() + ", \"s\")' > /dev/null 2>&1 &"
            Popen([command], shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)
            f.close()

        if (sys.argv[1] == '-b'):
            f = open('database/bitcoin', 'r')
            potion.getBalances(f.read())
            f.close()

        if (sys.argv[1] == '-a'):
            f = open('database/bitcoin', 'r')
            with open("database/addresses", "r") as ins:
                it = 1
                snodes = int(f.read())
                print ""
                for line in ins:
                    if (snodes < it ):
                        print "Address Monitor: " + line[:len(line)-1]
                    else:
                        print "Address " + str(it) + ": " + line[:len(line)-1]
                        it += 1
            print ""

def printProgressBar(iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)

    sys.stdout.write('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix))
    sys.stdout.flush()

    if iteration == total:
        print " Done!\n"

main()