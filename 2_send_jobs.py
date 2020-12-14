#!/usr/bin/env python3
"""
Sends all jobs with status Failed or Vanished to the cluster.
"""

import os
import sys
import re
from helper import *

#REFRESH THE job status files again
print("Updating job statuses..")
os.system("1_update_jobs.py")

#READ FAILED AND VANISHED JOBS TO LISTS
if os.path.exists("failedJobs.txt"):
	f = open("failedJobs.txt", "r")
	failedJobs = [line.rstrip('\n') for line in f]	#strip the newline characters
else:
	failedJobs=[]

if os.path.exists("deletedJobs.txt"):
	f = open("deletedJobs.txt", "r")
	failedJobs += [line.rstrip('\n') for line in f]	#strip the newline characters


if os.path.exists("vanishedJobs.txt"):
	f = open("vanishedJobs.txt", "r")
	vanishedJobs = [line.rstrip('\n') for line in f]	#strip the newline characters
else:
		vanishedJobs=[]

#CLEAN FAILED JOBS
print("Cleaning failed...")
for job in failedJobs:
	clean(job)

#RESEND FAILED JOBS
print("Sending failed...")
count=1
for job in failedJobs:
	print("{0} {1}".format(count, job))
	send(job)
	count+=1


#RESEND VANISHED jobs
print("\nSending vanished...")
for job in vanishedJobs:
	print("{0} {1}".format(count, job))
	send(job)
	count+=1

if count>0:
	print("Attempted to send {0} jobs.".format(len(vanishedJobs)+len(failedJobs)))
else:
	print("No jobs to send.")