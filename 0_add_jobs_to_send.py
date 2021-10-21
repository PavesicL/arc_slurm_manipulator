#!/usr/bin/env python3
"""
Given a general job name and a list of parameters from nameFile, takes parameter values as an input and appends all requested job names to jobsToSend.txt.
"""

import sys
import re
from helper import *

# THIS IS ALL PARSING THE INPUT AND PRINTING/CHECKING IF EVERYTHING IS OK ###########################################################################

jobname, paramDict = getParamsNameFile("nameFile")

print(jobname)
print([(i.name, i.sweeptype) for i in paramDict.values()])

#The required input is at least three values for the sweep parameters (min, max, step) and at least one value for the case parameters.
smallestInputLen = 1 #start at 1 as len(sys.argv) is always at least 1 (sys.argv[0] is the name of the script)
outputString = " "
for param in paramDict.values():
	paramname = param.name
	sweeptype = param.sweeptype		
	
	outputString += paramname+" "
		
	if sweeptype == "case":
		smallestInputLen+=1
		outputString += paramname+"s "

	elif sweeptype == "sweep":
		smallestInputLen+=3
		outputString += paramname+"_min " + paramname+"_max " + paramname+"_step "

	elif sweeptype == "logsweep":
		smallestInputLen+=3
		outputString += paramname+"_min " + paramname+"_max " + paramname+"_numstep "

	elif sweeptype == "relation":	#IF IT STARTS WITH =, THEN THIS PARAMETER HAS SOME EQUALITY/RELATION TO OTHER PARAMS	
		smallestInputLen+=1
		outputString += "relation "

if len(sys.argv) < smallestInputLen:
	print("Usage: " + str(sys.argv[0]) + outputString)
	print("Params with relation have to be at the end of the nameFile param list!")
	exit()


#PARSE INPUT
#Iterate over the input, if the input matches the name of a parameter, append all the following numbers into a key od a dictionary.
casesDict = {}
for i in range(1, len(sys.argv)):
	skip=False	

	for param in paramDict:

		if sys.argv[i] == param:
			whichParam = param
			casesDict[whichParam]=[]
			skip = True	#when we find a parameter name, skip this instance of i
	
	if not skip:	#if we have not found a parameter name at this i, append the number to the corresponding list in casesList
		casesDict[whichParam].append(sys.argv[i])	



#SET VALUES OF PARAMETERS FROM THE casesDict AND PRINT THEM OUT
print("\nThe sweep is over parameters: ")
for p in paramDict.values():
	p.set_values(casesDict[p.name])
	print("{}: {}".format(p.name, p.values))


# GENERATE ALL JOB NAMES AND SAVE THEM TO A FILE ####################################################################################################

jobNameList = getJobnameList(jobname, [p for p in paramDict.values()])

add = input("Add {} jobs to jobsToSend.txt? [y/n]\n".format(len(jobNameList)))

if add=="y":
	count=0
	with open("jobsToSend.txt", "a+") as newF:

		for job in jobNameList:		
			newF.write(job+"\n")
			count+=1

	print("{0} jobs added to jobsToSend.txt.".format(count))