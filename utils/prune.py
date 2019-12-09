
import sys



with open (sys.argv[1]) as f:
    lines = f.readlines()

output = []

nodes = [
    'zotacM18', 
    'zotacD4', 
    'zotacC2',
    'zotacE3', 
    'zotacC1', 
    'zotacG6', 
    'zotacB2', 
    'zotacH1',
    'zotacF1',
    'zotacJ3', 
    'zotacK6', 
    'zotacK4', 
    'zotacC4', 
    'zotacC3', 
    'zotacF4',
    'zotacE4',
    'zotacG4',
    'zotacG3',
    'zotacI1',
    'zotacI3',
    'zotacI4',
    'zotacE2',
    'zotacG1',
    'zotacI2',
    'zotacH3',
    'zotacK3'
]

for line in lines:
    line_good = True

    for node in nodes:
        if node in line:
            line_good = False

    if line_good:
        output.append(line)

        

for line in output:
    print line