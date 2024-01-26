#!/usr/bin/env python3

import os
import helper
"""
Restarts all failed jobs.
The procedure is code dependent and should be given in the continue_script.
"""

if os.path.exists("failedJobs.txt"):
	f = open("failedJobs.txt", "r")
	failedJobs = [line.rstrip('\n') for line in f]
else:
	failedJobs=[]

print(f"Found {len(failedJobs)} failed jobs.")

for job in failedJobs:
    print()
    print(job)
    helper.continue_job(job=job, scriptname="SAMPLEcontinueScript")

print(f"Restarted {len(failedJobs)} jobs.")