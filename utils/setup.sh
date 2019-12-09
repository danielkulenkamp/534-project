#!/bin/bash

echo "Did you remember to update the node_info.txt file?"
echo

cat node_info.txt

echo
echo "Does this look correct? (yes/no)"

read var
echo


if [ "$var" == "yes" ]; then
	#echo "Please enter your password for the testbed: "
	#read password
	#echo 

	sudo apt-get install -y fabric iputils-clockdiff inetutils-traceroute tshark

	#echo "Setup completed. Would you like to setup multihop? (yes/no)"
	#read answer
	#echo

	#if [ "$answer" == "yes" ]; then
	#	fab --password=$password setup_multihop
	#else
	#	echo "Don't forget to setup multihop if doing multihop experiments"
	#	echo
	#	echo "Don't forget to time sync with ptpd!"
	#fi
else
	echo "Please update the node_info.txt file before proceeding."
fi



 

