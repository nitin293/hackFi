#!/bin/bash

[ -d "./tmp" ] && echo "Directory ./trash exists." || mkdir ./tmp
sudo apt-get update -y
sudo apt-get install xterm -y
sudo apt-get install rfkill -y
sudo apt-get install ethtool -y
sudo apt-get install aircrack-ng -y
sudo apt-get install python3 -y
sudo apt-get install python3-pip -y
sudo pip3 install pandas
