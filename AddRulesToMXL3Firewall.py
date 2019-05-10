"""
Copyright (c) 2019 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""
# This script retrieves a Meraki MX L3 Firewall rule from the file NewRuleToAdd.txt and adds it to all
# networks in the Org. The rule inserted only specifies the Destination IPs (destCidr field) and uses
# the comment specified in the first line of the input file for the "comment" field of the rule
# all other parameters for the rule are specified in templateRuleDict below for all insertions.

from meraki import meraki
import time
import sys
import config

templateRuleDict= {
        "comment": "",
        "policy": "deny",
        "protocol": "any",
        "srcPort": "Any",
        "srcCidr": "Any",
        "destPort": "Any",
        "destCidr": "",
        "syslogEnabled": True
    }

from meraki import meraki

# sample in case you want to obtain the orgs programmatically
#myOrgs = meraki.myorgaccess(config.meraki_api_key, True)
#print(myOrgs)

#first read the rule you want to add from the NewRuleToAdd.txt file
#make sure the first line of the file only contains the comment for the rule to add
#and the second line contains a comma separated list of IP addresses in dot-decimal notation
with open ("NewRuleToAdd.txt", "r") as myfile:
    theRuleData = myfile.read().splitlines()
#check for exactly 2 lines in the file
if len(theRuleData)!=2:
    print("Input file must have exactly 2 lines!")
    sys.exit(1)
#first retrieve the comment for the rule from the first line
theRuleComment=theRuleData[0]
#now retrieve the comma separated list of IP addresses to put in the rule
theRuleIPs=theRuleData[1]
# The following code will do a quick sanity check for correct formatting of the IP addresses in
# dot-decimal notation by counting number of periods and commas. It does not make sure each one is
# actually composed of 4 decimal numbers though. For a stronger , some of the suggestions here could be
# implemented https://stackoverflow.com/questions/11264005/using-a-regex-to-match-ip-addresses-in-python/11264056
numPeriods=theRuleIPs.count(".")
numCommas=theRuleIPs.count(",")
if numPeriods%3!=0:
    print("There does not appear to be any IP Addreses in the second line of the input file!")
    sys.exit(1)
if numPeriods/3 != numCommas+1:
    print("Number of commas in IP address list does not match number of IP addresses!")
    sys.exit(1)

#compose the new rule to add in the right format using a Dict template specified earlier
theRuleToAddDict=templateRuleDict
theRuleToAddDict["comment"]=theRuleComment
theRuleToAddDict["destCidr"]=theRuleIPs

#obtain all networks in the Org specified by the config variable
myNetworks = meraki.getnetworklist(config.meraki_api_key, config.meraki_org_id, None, True)

print("About to insert the following rule:")
print(theRuleToAddDict)
print("into the following networks:")
for theNetwork in myNetworks:
    theNetworkid = theNetwork["id"]
    theNetworkname = theNetwork["name"]
    print(theNetworkid, "  ",theNetworkname)
#stop the script if the operator does not agree with the operation being previewed
if not input("Procced? (y/n): ").lower().strip()[:1] == "y": sys.exit(1)


for theNetwork in myNetworks:
    theNetworkid = theNetwork["id"]
    #get the rules
    theMXL3FirewallRules=meraki.getmxl3fwrules(config.meraki_api_key, theNetworkid, True)
    #removing any marked as "Default rule" to avoid duplicates
    theMXL3FirewallCleanRules=[]
    for theRule in theMXL3FirewallRules:
        if theRule["comment"]!="Default rule":
            theMXL3FirewallCleanRules.append(theRule)
    #add the new cleaned rule
    theMXL3FirewallCleanRules.append(theRuleToAddDict)
    #update the rules with the new one added
    print("Updating rules for Network ID: "+theNetworkid+"...")
    meraki.updatemxl3fwrules(config.meraki_api_key, theNetworkid, theMXL3FirewallCleanRules,False,False)
    #Uncomment line below if you wish to provide confirmation for each Network
    #if not input("Continue? (y/n): ").lower().strip()[:1] == "y": sys.exit(1)
    #need to make sure we do not send more than 5 API calls per second for this org
    #so sleep 500ms since we are making 2 API calls per loop
    time.sleep(0.5)

print("Done!")