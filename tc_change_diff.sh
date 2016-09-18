#!/bin/bash

rate=0.15Mbit
rate2=0.03Mbit
rate3=0.001Mbit

function change_qdisc {
    dev=$1

    tc class change dev $dev classid 1:10 parent 1:1 htb rate $rate2 ceil $rate
    tc class change dev $dev classid 1:11 parent 1:1 htb rate $rate3 ceil $rate
    echo classes changed

}

change_qdisc s0-eth1
change_qdisc s0-eth2
