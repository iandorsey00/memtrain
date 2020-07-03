import argparse
import csv

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
