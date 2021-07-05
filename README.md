# Add Meraki MX L3 Firewall Rule to Networks
This is a simple Python script that takes a NewRuleToAdd.txt file as input to add one rule with all the IP addresses from the list to each Network in the Org using the Meraki API. 
Before going off to add the rules, it will print out to console a summary of the IPs to add to the new rule, the ticket number and the list of all networks it will add them to.
It will then ask for confirmation from the operator of the script.


## Dependencies and initial setup:

Python 3.6 with the following modules installed: 

1. requests
2. meraki


More details on the meraki module here: 
https://github.com/meraki/dashboard-api-python
https://developer.cisco.com/meraki/api-v1/#!overview

 
You can typically install those modules with the following commands: 

pip install requests

pip install meraki

You need to have a file named config.py in the same directory as the AddRulesToMXL3Firewall.py
script with the definition of the Meraki API key to use to run the code as well as the Org ID for
the Organanization for which you want to change the rules for all Networks.

Example of content of the **config.py** file you must create: 
``` 
meraki_api_key = "yourMerakiAPIKey"
meraki_org_id = "yourOrgID"
```

You also need to have the input file named NewRuleToAdd.txt in the same directory as the **AddRulesToMXL3Firewall.py**
It should only have two lines:
1. Comment to use for new rule to be added
2. comma separated list of IP addresses in dot-decimal notation

Example of content of the **NewRuleToAdd.txt** file you must create:

``` 
Case323423
40.17.41.118,40.17.41.119
```

## Running the code:

python3 AddRulesToMXL3Firewall.py

You will be prompted for confirmation before proceeding with the overall operation. 
You will also be prompted on a per Network basis if you wish to proceed with adding the rules

If you wish to remove this last confirmation so the script can run for all Networks
without interruption, look for the comment below in the **AddRulesToMXL3Firewall.py**
file and comment the line below it by adding # as the first character of the line

_"#Comment line below if you wish to skip confirmation for each Network"_



