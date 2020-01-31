#!/bin/bash

#Environment
numnodes=$1
numconns=$2
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

 echo "Running btcnode$n"
 mkdir $datadir
 
 run $btcd $net -datadir=$datadir -port=$(port n) -rpcport=$(rport n) -debug=net -logips $@ -daemon
}

function runmalnode(){
  echo "Running malicious node"
  tmp=$btcd
  btcd=$btcd-malicious
  runnode $@
  btcd=$tmp
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

 echo "Connecting $n1 to $n2"
 run $btccli $net -rpcport=$(rport $n1) -datadir=$(ddir $n1) addnode 127.0.0.1:$(port $n2) onetry

 if [ $? = 0 ]; then
  CONNS[$n1$n2]=true
 fi

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
    runmalnode $i
  else
    runnode $i
  fi
  sleep 2
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

  sleep 5
done


#Run Monitor
m=$((numnodes + 10))
runnode $m -pocmon
sleep 3
for i in $(seq 1 $numnodes)
do
 addconn $m $i
 sleep 1
done

#Get Nodes Info
sleep 5
echo "GETNETNODESINFO"
nodecli $m getnetnodesinfo

#Wait 5 secs
sleep 5
echo "GETNETNODESINFO (5 secs after)"
nodecli $m getnetnodesinfo

#Remove node and wait for POC procedure to repeat
nodecli $numnodes stop
sleep 5
echo "GETNETNODESINFO"
nodecli $m getnetnodesinfo
sleep 5

#Stop Nodes
numnodes=$(($numnodes - 1));
for i in $(seq 1 $numnodes)
do
  nodecli $i stop
done
nodecli $m stop
sleep 3

for i in $(seq 1 $numnodes)
do
  echo "__________ LOG Node$i __________" > log.txt
  cat poctest/btcnode$i/regtest/debug.log | grep '\[POC\]' >> log.txt
done
echo "__________ MONITOR LOG __________" >> log.txt
cat poctest/btcnode$m/regtest/debug.log | grep '\[POC\]' >> log.txt
echo "VERIFIED PEERS:" >> log.txt
cat poctest/btcnode$m/regtest/debug.log | grep 'verified' >> log.txt

exit 0

