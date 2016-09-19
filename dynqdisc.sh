rm s0-eth*
python tcshow.py --intf s0-eth1,s0-eth2 --iter 4000 --ipblock '10.0.0.2/32' --portRange '5001-5002' --cToS True --linkCap '0.15'
