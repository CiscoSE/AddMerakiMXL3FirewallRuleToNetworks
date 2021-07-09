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

import meraki
import time
import sys
import config
import requests


dashboard = meraki.DashboardAPI(api_key=config.meraki_api_key)

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

templateRuleDictNoSyslog= {
        "comment": "",
        "policy": "deny",
        "protocol": "any",
        "srcPort": "Any",
        "srcCidr": "Any",
        "destPort": "Any",
        "destCidr": ""
    }

#allow or dissalow adding duplicate firewall rules
allowDuplicates=False

#from meraki import meraki

# Return configured Syslog Servers for a network
# https://dashboard.meraki.com/api_docs#list-the-syslog-servers-for-a-network
def getsyslogservers(apikey, networkid, suppressprint=False):
    calltype = 'Syslog servers'
    geturl = '{0}/networks/{1}/syslogServers'.format(
        str(meraki.base_url), str(networkid))
    headers = {
        'x-cisco-meraki-api-key': format(str(apikey)),
        'Content-Type': 'application/json'
    }
    dashboard = requests.get(geturl, headers=headers)
    result = meraki.__returnhandler(
        dashboard.status_code, dashboard.text, calltype, suppressprint)
    return result


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

#obtain all networks in the Org specified by the config variable
#myNetworks = meraki.getnetworklist(config.meraki_api_key, config.meraki_org_id, None, True)
myNetworks = dashboard.organizations.getOrganizationNetworks(config.meraki_org_id, total_pages='all')

#stop the script if the operator does not agree with the operation being previewed
print("About to insert the following IPs: ",theRuleIPs," in a rule with comment: "+ theRuleComment)
print("into the following networks:")
for theNetwork in myNetworks:
    theNetworkid = theNetwork["id"]
    theNetworkname = theNetwork["name"]
    print(theNetworkid, "  ",theNetworkname)
if not input("Procced? (y/n): ").lower().strip()[:1] == "y": sys.exit(1)


for theNetwork in myNetworks:
    theNetworkid = theNetwork["id"]
    #comment the 3 lines below if you do not want to filter out networks whose name matches that condition
    if theNetwork["name"].startswith('z') or theNetwork["name"].endswith('switch-wifi') or theNetwork["name"].endswith('camera') or theNetwork["name"].endswith('systems manager'):
        print("Skipping network named: ",theNetwork["name"], " because it starts with z or ends with switch-wifi, camera or systems manager" )
        continue

    print("Updating rules for Network ID: "+theNetworkid+" named: ",theNetwork["name"],"...")
    continueAnswer="y"
    #Comment line below if you wish to skip confirmation for each Network
    continueAnswer=input("Continue? yes, no or skip(y/n/s): ").lower().strip()[:1]
    if continueAnswer=="n":
        print("Bye!")
        sys.exit(1)
    elif continueAnswer=="s":
        print("Skipping Network ID: "+theNetworkid+" named: ",theNetwork["name"],"...")
        continue

    #get the rules
    # theMXL3FirewallRules=meraki.getmxl3fwrules(config.meraki_api_key, theNetworkid, True)
    theMXL3FirewallRules=dashboard.appliance.getNetworkApplianceFirewallL3FirewallRules(theNetworkid)
    # print("THE RULES:"+str(theMXL3FirewallRules))

    #retrieving the syslog servers to know which template to use
    #theSysLogServers=getsyslogservers(config.meraki_api_key, theNetworkid, True)
    theSysLogServers = dashboard.networks.getNetworkSyslogServers(theNetworkid)
    #print("Syslog Servers: ", theSysLogServers)

    # compose the new rule to add in the right format using the corresponding Dict template
    if theSysLogServers["servers"] == []:
        theRuleToAddDict = templateRuleDictNoSyslog
    else:
        theRuleToAddDict = templateRuleDict
    theRuleToAddDict["comment"] = theRuleComment
    theRuleToAddDict["destCidr"] = theRuleIPs

    #removing any marked as "Default rule" to avoid duplicates
    theMXL3FirewallCleanRules=[]
    for theRule in theMXL3FirewallRules["rules"]:
        if theRule["comment"]!="Default rule":
            #check to see if we allow duplicates. If not, then do not a rule if another one with the same comment exists
            if theRule["comment"]!=theRuleToAddDict["comment"] or allowDuplicates:
                theMXL3FirewallCleanRules.append(theRule)
            else:
                print("Skipping duplicate rule ",theRule["comment"])

    #add the new cleaned rule
    theMXL3FirewallCleanRules.append(theRuleToAddDict)
    print("CLEAN RULES:"+str(theMXL3FirewallCleanRules))

    #update the rules with the new one added
    #meraki.updatemxl3fwrules(config.meraki_api_key, theNetworkid, theMXL3FirewallCleanRules,False,False)
    updateResponse = dashboard.appliance.updateNetworkApplianceFirewallL3FirewallRules(theNetworkid, rules=theMXL3FirewallCleanRules)

    #need to make sure we do not send more than 5 API calls per second for this org
    #so sleep 500ms since we are making 2 API calls per loop
    time.sleep(0.5)

print("Done!")
