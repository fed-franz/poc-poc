#!/bin/bash

#Environment
numnodes=$1
numconns=$2
m=$((numnodes + 10))
m2=$((m + 1))
testdir=poctest
btcd=btcbin/bitcoind
btccli=btcbin/bitcoin-cli
net=-regtest
baseport=1900

omal=-malicious
runmalicious=true
malnum=2

declare -A CONNS 

### MACROS ###
port(){ 
 np=$1
 echo $((baseport + 10*np))
}

rport(){ 
 np=$1
 echo $((baseport + 10*np + 1))
}

ddir(){
 echo $testdir/btcnode$1
}

run(){
 echo $@
 $@
 return $?
}

### FUNCTIONS ###
function runnode() {
 n=$1
 shift
 datadir=$(ddir $n)

 if [ $n = $m ]; then
   echo "Running M"
 elif [ $n = $m2 ]; then
   echo "Running M2"
 else
   echo "Running N$n"
 fi

 mkdir $datadir 
 run $btcd $net -datadir=$datadir -port=$(port n) -rpcport=$(rport n) -debug=net -logips $@ -daemon
 sleep 4
}

function nodecli() {
 nc=$1
 shift

 run $btccli $net -rpcport=$(rport $nc) -datadir=$(ddir $nc) $@
}

function addconn() {
 n1=$1
 n2=$2

  ##TODO: Check n1 != n2 
 if [ ${CONNS[$n1$n2]} ] || [ ${CONNS[$n2$n1]} ]; then
  #echo "ERR: Nodes are already connected"
  return -1
 fi

 if [ $n1 = $m ]; then
   echo "Connecting M to N$n2"
 elif [ $n1 = $m2 ]; then
   echo "Connecting M2 to N$n2"
 else
   echo "Connecting N$n1 to N$n2"
 fi
 run $btccli $net -rpcport=$(rport $n1) -datadir=$(ddir $n1) addnode 127.0.0.1:$(port $n2) onetry

 if [ $? = 0 ]; then
  CONNS[$n1$n2]=true
 fi

 sleep 1

 return $?
}

##### START TEST #####

#Check connections are not above the limit (n(n-1))/2
maxconn=$(( numnodes*(numnodes-1) / 2 ))
if [ $numconns -gt $maxconn ]; then
 echo "ERR: Max connections = $maxconn"
 exit 1
fi

#Reset Test dir
rm -rf $testdir
mkdir $testdir

#Create Nodes
for i in $(seq 1 $numnodes)
do
  if [ $i = $malnum ] && [ $runmalicious = true ]; then
    runnode $i $omal
  else
    runnode $i
  fi
done

#Run Monitor and connect to all nodes
runnode $m -pocmon
for i in $(seq 1 $numnodes)
do
 addconn $m $i
done

#Run Monitor and connect to all nodes
runnode $m2 -pocmon
for i in $(seq 1 $numnodes)
do
 addconn $m2 $i
done


# TODO: if numnodes > 4 check at least one outbound per each node
#Create connections
for i in $(seq 1 $numconns)
do
  status=1

  #If addconn fails, try a different connection
  while [ $status -ne 0 ]
  do
    n1=$(($RANDOM % $numnodes + 1))
    n2=$(($RANDOM % $numnodes + 1))

    #Make sure n1 != n2
    while [[ ( "$n1" = "$n2" ) || ( "$runmalicious" = "true" && "$n1" = "$malnum" && "$n2" = "1" ) ]]
    do
      n2=$(($RANDOM % $numnodes + 1))
    done

    addconn $n1 $n2
    status=$?
  done
done

#Get Nodes Info
sleep 5
echo "GETNETNODESINFO"
nodecli $m getnetnodesinfo
nodecli $m2 getnetnodesinfo

#Remove node
removed=$(($RANDOM % $numnodes + 1))
echo "Removing node$removed"
nodecli $removed stop
sleep 2

echo "GETNETNODESINFO"
nodecli $m getnetnodesinfo
nodecli $m2 getnetnodesinfo
sleep 2

#Add new node
newnode=$(($numnodes + 1))
runnode $newnode
#Connect monitors to new node
addconn $m $newnode
addconn $m2 $newnode
#Create connections to new node
connadded=0
while [ $connadded -ne 1 ]
do
  for i in $(seq 1 $numnodes)
  do
    connect=$(($RANDOM % 6))

    #If addconn fails, try a different connection
    if [ $i -ne $removed ] && [ $connect -gt 1 ]; then
      connadded=1
      outbound=$(($RANDOM % 2))
      if [ "$outbound" = "1" ]; then
        addconn $newnode $i
      else
        addconn $i $newnode
      fi
    fi
  done
done
numnodes=$(($numnodes + 1))

sleep 5
echo "GETNETNODESINFO"
nodecli $m getnetnodesinfo
nodecli $m2 getnetnodesinfo

#Stop Nodes
#numnodes=$(($numnodes - 1));
for i in $(seq 1 $numnodes)
  do
    if [ $i -ne $removed ]; then
      nodecli $i stop
    fi
  done
  nodecli $m stop
  nodecli $m2 stop
  sleep 3

for i in $(seq 1 $numnodes)
do
  echo "__________ LOG Node$i __________" > log.txt
  cat poctest/btcnode$i/regtest/debug.log | grep '\[POC\]' >> log.txt
done
echo "__________ MONITOR LOG __________" >> log.txt
cat poctest/btcnode$m/regtest/debug.log | grep '\[POC\]' >> log.txt

exit 0

