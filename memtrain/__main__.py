import argparse
import csv

# Settings ####################################################################

## Boolean settings

### Levels

# Level 1 - Multiple choice questions
level1 = True
# Level 2 - Use a hint to respond
level2 = True
# Level 3 - Respond on your own
level3 = True

### Alias

# Alias
alias = True



# nquestions - Number of questions
nquestions = 0

title = ''

def lowercase_row(row):
    '''Make every string in a row lowercase'''
    return map(lambda x: x.lower(), row)

def load(csvfile):
    '''Load the CSV file'''
    out = []

    with open(csvfile) as cf:
        csvreader = csv.reader(cf)
        for row in csvreader:
            out.append(row)

    return out

def train(args):
    '''Begin training'''
    database = load(args.csvfile)

    for row in database:
        if sum(row) == 1:
            if lowercase_row(row[0]).startswith('settings:')


    print(database)

###############################################################################
# Argument parsing with argparse

# Create the top-level argument parser
parser = argparse.ArgumentParser(
    description='A program for better memory training')
parser.set_defaults(func=train)

# Create arguments
parser.add_argument('csvfile', help='The CSV file to load')

# Parse arguments
args = parser.parse_args()
args.func(args)
