#!/usr/bin/env python3
"""
Reads the output of either arcstat or squeue and parses the job statuses. Saves the data to .txt files by categories.
"""

import os
import sys
import re
from helper import *

#get a regex general form of the name
name, _ = getParamsNameFile("nameFile")
#regexName = re.sub("{[0-9]+}", "(-*[0-9]+\.*[0-9]*)", name)	#replace all instances of {number} in the name with ([0-9]+.*[0-9]*), which matches floats and ints
regexName = re.sub("{[0-9]+}", "([+-]?[0-9]+(?:\.?[0-9]*(?:[eE][+-]?[0-9]+)?)?)", name)
#READ THE FILE WITH ALL REQUESTED JOBS TO A LIST
f = open("jobsToSend.txt", "r")
jobsToSend = [line.rstrip('\n') for line in f]	#strip the newline characters


#SAVE THE INFORMATION ABOUT THE JOBS FROM THE QUEUE TO statJobs.txt
print("Getting job info..")
jobStatuses = get_StatJobs(regexName)	#refreshes the file statJobs.txt, depends whether the system variable WHICHSYSTEM is slurm or arc

#GET VANISHED JOBS AS A COMPARISON BETWEEN jobsToSend.txt and jobs in jobStatuses
for job in jobsToSend:
	if not job in jobStatuses:
		jobStatuses[job] = "Vanished"

######################################################################################
#WRITE THE CONTENT OF jobStatuses TO FILES

def appendLineToFile(line, file):
	with open(file, "a+") as f:
		f.writelines(line+"\n")
	return None

countDict = {"Queuing":0, "Running":0, "Finished":0, "Failed":0, "Vanished":0, "Saved":0, "Deleted":0}

#clean the files if they exist
for typ in countDict:
	fileName = typ.lower() + "Jobs.txt"
	
	if os.path.exists(fileName):
		os.remove(fileName)

other=0
#this writes each jobname to corresponding file, eg. a job with status Running is appended to runningJobs.txt
for jobname in sorted(jobStatuses):
	appendLineToFile(jobname, jobStatuses[jobname].lower()+"Jobs.txt")
	try:
		countDict[jobStatuses[jobname]] += 1
	except KeyError:
		other+=1

print("Updated lists.")
print("There is: {0} running, {1} queueing, {2} finished, {3} failed, {4} deleted, {5} vanished and {6} saved jobs, {7} unrecognized; for a total of {8} jobs."
	.format( countDict["Running"], countDict["Queuing"], countDict["Finished"], countDict["Failed"], countDict["Deleted"], countDict["Vanished"], countDict["Saved"], other, other + sum(countDict.values()) ))