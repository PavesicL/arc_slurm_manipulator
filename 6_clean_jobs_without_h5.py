#!/usr/bin/env python3
"""
Sends all jobs with status Failed or Vanished to the cluster.
"""

import os
from shutil import rmtree
from helper import *

#REFRESH THE job status files again
print("Updating job statuses..")
os.system("1_update_jobs.py")

#ITERATE OVER ALL FOLDERS IN results/ AND SAVE THE NAMES OF THE ONES THAT DO NOT INCLUDE A FILE WITH .h5
brokenJobs = []
for job in os.listdir("results/"):
	broken = True	

	for file in os.listdir("results/" + job):
		if file.endswith(".h5"):
			broken = False
	
	if broken:
		brokenJobs.append(job)

brokenJobs.sort()

numJobs = len(brokenJobs)

#DELETE THESE JOBS
print()
if numJobs == 0:
	print("0 broken jobs found.")
	exit()

else:
	ask = input("{} broken jobs found. Delete them all? 'P' for print. [y/n/P]\n".format(len(brokenJobs)))

	if ask == "P":
		for job in brokenJobs:
			print(job)

	if ask == "y":
		count = 0
		for job in brokenJobs:
			rmtree("results/" + job)
			count += 1

		print(f"{count} jobs deleted.")

