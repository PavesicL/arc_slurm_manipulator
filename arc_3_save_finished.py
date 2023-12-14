#!/usr/bin/env python3
"""
Saves all finished jobs into the folder /results, into subfolders named by the job names.
"""

import os
import sys
import re

#Allow usage of the -f switch
try:
	if sys.argv[1]=="-f":
		print("Got argument -f, overwriting any previously saved jobs.")
except IndexError:
	pass

force=False
if len(sys.argv) == 2:
	if sys.argv[1] == "-f":
		force=True

print("Updating jobs..")
os.system("1_update_jobs.py")
print()

#Get the finished jobs and save them to folders according to job names (-J flag), and inside the folder results/ (-D results). Overwrite previous jobs if given the -f flag.
print("Downloading..")
count=0
with open("finishedJobs.txt", "r") as finF:

	for name in finF:
		count+=1
		print()
		print("{0} {1}".format(count, name))
		if force:
			os.system("arcget -J -D results -f -t 100 {0}".format(name))

		else:
			os.system("arcget -J -D results {0}".format(name))

print("DONE")