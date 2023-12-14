#!/usr/bin/env python3

"""
Functions used within the arc_manipulator scripts.
"""

import os
import re
import sys
import math
#import parser THIS IS DEPRECATED! SOLVE THE PROBLEM WITH relation PARAMS
import itertools

#####################################################################################################

def myarange(start, stop, step):
	"""
	Instead of the np.arange function.
	"""
	ll=[]
	numsteps = int(round((stop-start)/step, 1))

	for i in range(numsteps):
		ll.append(round(start+i*step, 5))

	ll.append(stop)

	return ll

#####################################################################################################
"""
The parameter class is used for two things:
	 when sending jobs, it is used to generate a parameter dictionary from a jobname. There we want to know the parameter name and its single value.
		This is then iterated over all
"""

class parameter:

	def __init__(self, name, sweeptype):
		self.name = name
		self.sweeptype = sweeptype

		self.values = None 	#defined in set_values()

	def set_single_value(self, value):
		"""
		Set the variable values to be a single float. Used in send_jobs.
		"""
		self.values = value

	def set_values(self, inVals):
		"""
		Sets the values of the parameter when given as in add_jobs_to_send.
		"""

		self.checkInVals(inVals)	#check if everything is ok

		if self.sweeptype == "case":
			self.values = [float(i) for i in inVals]

		elif self.sweeptype == "sweep":
			start, stop, step = float(inVals[0]), float(inVals[1]), float(inVals[2])
			self.values = [round(float(i), 10) for i in myarange(start, stop, step)]

		elif self.sweeptype == "logsweep":
			#this is a list of [start, start * r, start * r^2, ..., start * r^N], where N = numstep - 1. This gives r = (stop / start) ^ (1/N).
			start, stop, numstep = float(inVals[0]), float(inVals[1]), int(inVals[2])
			r = (stop/start)**(1/(numstep-1))
			self.values = [ round(start * r**i, 10) for i in range(numstep) ]

		elif self.sweeptype == "relation":
			self.values = inVals[0]

		return None

	def checkInVals(self, inVals):
		"""
		Checks if the lenght of inVals is OK, namely wheter it corresponds with what is expected from sweeptype.
		"""
		if self.sweeptype=="case" and len(inVals)<1:
			print("The parameter {0} is type case but did not get 1 value or more, but {1}!".format(self.name, len(inVals)))
			exit()

		elif self.sweeptype=="sweep" and len(inVals)!=3:
			print("The parameter {0} is type sweep but did not get 3 values, but {1}!".format(self.name, len(inVals)))
			exit()

		elif self.sweeptype=="logsweep" and len(inVals)!=3:
			print("The parameter {0} is type logsweep but did not get 3 values, but {1}!".format(self.name, len(inVals)))
			exit()

		elif self.sweeptype=="relation" and len(inVals)!=1:
			print("The parameter {0} is type relation but did not get 1 value, but {1}!".format(self.name, len(inVals)))
			exit()

		return None




#####################################################################################################

def nameToRegex(name):
	"""
	Replace all instances of {number} in the name with ([0-9]+.*[0-9]*), which matches floats and ints
	"""
	#OLD return re.sub("{[0-9]+}", "(-*[0-9]+\.*[0-9]*)", name)	#replace all instances of {number} in the name with ([0-9]+.*[0-9]*), which matches floats and ints

	return re.sub("{[0-9]+}", "([+-]?[0-9]+(?:\.?[0-9]*(?:[eE][+-]?[0-9]+)?)?)", name)	#replace all instances of {number} in the name with a regex which matches floats and ints. Also allows for scientific notation, eg. 1e-6.

#####################################################################################################

def getParamsNameFile(file):
	"""
	Reads the nameFile, and returns a generic jobname and a dictionary of parameters,
	where key is the parameter name and value is its sweeptype (sweep, case or relation).
	"""

	paramsDict = {}

	paramsCheck = False
	with open(file, "r") as f:
		for line in f:
			line = line.strip()	#strip the leading and trailing whitespace
			if len(line)==0:
				continue

			a = re.search("name\s*=\s*(.*)", line)

			b = re.search("params\s*{", line)
			c = re.search("}\s*endparams", line)

			d = re.search("(\w*)\s*(\w*)", line)

			if line[0] == "#":	#this line is a comment
				pass
			if a:	#this line has the name, save it
				name = a.group(1)
			if b:	#we are in the part of the file with the params info
				paramsCheck=True
				continue
			if c:	#we are past the part of the file with the params info
				paramsCheck=False

			if paramsCheck and d:	#parse parameters
				param, sweeptype = d.group(1), d.group(2)
				paramsDict[param] = parameter(param, sweeptype)

		return name, paramsDict

def getBatchParamsNameFile(file):
	"""
	Reads the parameter that are to be written into the sbatch file from nameFile. Also NUM_OMP_THREADS!
	"""

	batchparamsCheck = False
	batchParamsDict = {}

	with open(file, "r") as f:
		for line in f:

			stripline = line.strip()
			if len(stripline)>0 and stripline[0] == "#":	#comment
				continue

			a = re.search("batch{", line)
			b = re.search("}endbatch", line)

			if a:
				batchparamsCheck = True
			if b:
				batchparamsCheck = False

			if batchparamsCheck:
				c = re.search("(.*) (.*)", line.strip())	#this should match all parameters, but also probably matches a lot of other stuff, be careful!
				if c:
					name = c.group(1)
					val = c.group(2)

					batchParamsDict[name] = val

	return batchParamsDict

def nameToParamsVals(jobname, nameFile="nameFile"):
	"""
	Given the jobname, returns a dictionary with parameters and their values.

	First recover a list of parameters from the nameFile.
	Next, by comparing it to regexName, recover the values of these parameters
	and assign these values to keys of the paramDict dictionary.
	"""

	name, paramsDict = getParamsNameFile(nameFile)
	regexName = nameToRegex(name)

	i=0
	a = re.search(regexName, jobname)	#match the regexname with the jobname
	for p in paramsDict.values():
		i+=1
		value = float(a.group(i))

		p.set_single_value(value)

	return paramsDict

def editInputFile(paramDict):
	"""
	Copies the SAMPLEinputFile, except the parameters in paramDict, which are changed to their values.
	"""
	#DMRG SPECIFIC!

	DELTA = getDeltaFromNameFile("nameFile")

	#THIS IS UGLY AND SHOULD BE CHANGED!
	for paramName in paramDict:
		if paramName == "Ec" or paramName == "Ec1" or paramName == "Ec2":
			p = paramDict[paramName]
			p.set_single_value(p.values * DELTA)

	with open("SAMPLEinputFile", "r") as sampleF:
		with open("inputFile", "w+") as newF:
			for line in sampleF:
				written=0	#whether the line was already written to the new file

				#iterate over all params - check if one of them matches the line, then overwrite it
				for p in paramDict.values(): 	#p.values() is a list, but we know that it only has a single element - the value of the parameter.

					if re.search("^"+p.name+"\s*=", line.strip()):
						newF.write("	"+p.name+" = {0}\n".format(p.values))
						written=True

				if not written:
					newF.write(line)
	return None

def editSendJobxrsl(jobname):
	"""
	Creates a new sendJob.xrsl file, where only the jobname is updated.
	"""

	with open("SAMPLEsendjob.xrsl", "r") as oldF:
		with open("sendjob.xrsl", "w+") as newF:

			for line in oldF:
				if re.search("jobname=", line):
					newF.write('(jobname="{0}")\n'.format(jobname))
				else:
					newF.write(line)

	return None

def writeBatchScript(batchDict, jobname):
	"""
	Writes the batch script to submit the job with.
	"""
	WHICHSYSTEM = os.environ["WHICHSYSTEM"]
	scriptname = "script"
	specialParams = ["OMP_NUM_THREADS", "ml", "path", "singularityPath"]	#these parameters are not written in the SBATCH syntax, but have to be specified alternatively

	#create the sendJob file
	with open("results/{0}/sendJob".format(jobname), "w") as job:
		job.writelines('#!/bin/bash\n')
		job.writelines('#SBATCH --job-name={0}\n'.format(jobname))

		for param in batchDict.keys():
			val = batchDict[param]
			if not param in specialParams:
				#write the params in the SBATCH syntax
				job.writelines('#SBATCH --{0}={1}\n'.format(param, val))

		if WHICHSYSTEM == "slurmmaister" or WHICHSYSTEM == "slurmNSC":
			if not "singularityPath" in batchDict:
				print("Singularity path not given! Enter singularityPath into nameFile; it is probably:")
				print("/ceph/grid/home/lukap/containers/foss2020_etc.sif")
				exit()

			if "path" in batchDict and "OMP_NUM_THREADS" in batchDict:
				job.writelines("SINGULARITYENV_OMP_NUM_THREADS={0} SINGULARITYENV_PREPEND_PATH={1} singularity exec {2} ./{3}\n"
																												.format(batchDict["OMP_NUM_THREADS"], batchDict["path"], batchDict["singularityPath"], scriptname))
			elif "path" in batchDict:
				job.writelines("SINGULARITYENV_PREPEND_PATH={0} singularity exec {1} ./{2}\n".format(batchDict["path"], batchDict["singularityPath"], scriptname))
			elif "OMP_NUM_THREADS" in batchDict:
				job.writelines("SINGULARITYENV_OMP_NUM_THREADS={0} singularity exec {1} ./{2}\n".format(batchDict["OMP_NUM_THREADS"], batchDict["singularityPath"], scriptname))

			else:
				job.writelines("singularity exec /ceph/sys/singularity/gimkl-2018b.simg {0}\n".format(scriptname))


		elif WHICHSYSTEM == "slurmspinon" or WHICHSYSTEM == "slurmvega":
			if "path" in batchDict:
				job.writelines("export PATH={0}:$PATH\n".format(batchDict["path"]))
			if "OMP_NUM_THREADS" in batchDict:
				job.writelines("export OMP_NUM_THREADS={0}\n".format(batchDict["OMP_NUM_THREADS"]))
			if "ml" in batchDict:
				job.writelines("ml "+ batchDict["ml"] + "\n")

			job.writelines("./{}\n".format(scriptname))


		else:
			print("Environment variable WHICHSYSTEM is not correct! It has to be one of slurmmaister, slurmmaisterspinon, slurmNSC!")
			print("Currently, it is: {}".format(WHICHSYSTEM))
			exit()


	return None

def getDeltaFromNameFile(nameFile):

	with open(nameFile, "r") as f:
		for line in f:
			a = re.search("DELTA\s*=\s*(.*)", line.strip())

			if a:
				DELTA = float(a.group(1))
				return DELTA

#####################################################################################################
#THESE FUNCTIONS TAKE CARE OF THE PARAMETER VALUES WHICH ARE RELATED TO OTHER PARAMS

def addRelationsToList(allCombinations, params):

	for i in range(len(allCombinations)):
		evaluatedRelations=[]
		for p in params:
			if p.sweeptype == "relation":
				evaluatedRelations.append(evalRelation(p.values, params, allCombinations[i]))

		allCombinations[i] = list(allCombinations[i]) + evaluatedRelations

	return allCombinations


def evalRelation(relation, params, vals):
	"""
	Evaluates a relation, given from parameter names and their values.
	relation: a relation to evaluate and return
	params: a list of parameters
	vals: a list of values of these parameters
	"""
	res = eval(relation, {params[i].name : vals[i] for i in range(len(vals))})
	res = round(res, 8)
	return res

def getJobnameList(genericName, params):

	noRelParams=[]	#create a list of params without the ones with relation
	for p in params:
		if p.sweeptype != "relation":
			noRelParams.append(p.values)

	allCombinations = list(itertools.product(*noRelParams))
	if len(allCombinations) < 20:
		print(allCombinations)
	res = addRelationsToList(allCombinations, params)

	jobList=[]
	for r in res:
		jobList.append(genericName.format(*r))

	return jobList

#####################################################################################################
#FUNCTIONS FOR UPDATING JOBS

def get_StatJobs(regexName):

	WHICHSYSTEM = os.environ["WHICHSYSTEM"]

	if WHICHSYSTEM == "arc":
		jobStatuses = getJobsArc(regexName)

	elif re.match("slurm.*", WHICHSYSTEM):
		jobStatuses = getJobsSlurm(regexName, WHICHSYSTEM)

	else:
		print("The environment variable WHICHSYSTEM is not set correctly! Has to be one of: arc, slurmspinon, slurmmaister, slurmNSC.")
		exit()

	return jobStatuses

def getJobsArc(regexName):
	"""
	Refreshes statJobs.txt and reads the arcstat output.
	Returns a dictionary of all jobs and their statuses.
	"""

	#REFRESH THE statJobs.txt FILE
	os.system("arcstat -a  > statJobs.txt")

	#GET A JOB LIST FROM THE CLUSTER WITH CURRENT JOB STATUS
	#jobStatuses is a dictionary, keys are all job names, values are job statuses. jobStatuses.keys() is directly comparable with jobsToSend.txt
	jobStatuses = {}
	with open("statJobs.txt", "r") as jobsF:

		here=0
		for line in jobsF:

			if here==0:
				a = re.search("("+regexName+")", line)
				if a:
					here=1
					name = a.group(1)

			if here==1:
				a = re.search("State: (.*)", line)
				if a:
					state = a.group(1)
					here = 0
					jobStatuses[name] = state #all possible statuses are here http://manpages.ubuntu.com/manpages/bionic/man1/arcstat.1.html. Typically, all jobs are Queuing, Running, Failed or Finished.

	#PARSE THE SAVED JOBS TOO
	for folder in os.listdir(("results/")):
		jobStatuses[folder] = "Saved"

	return jobStatuses

def getJobsSlurm(regexName, WHICHSYSTEM):
	"""
	Refreshes statJobs.txt and reads the squeue -u username output.
	Returns a dictionary of all jobs and their statuses. Statuses mimic the ARC nomenclature.
	Jobs are finished when there is a DONE file in their folder! Each slurm script has to include && touch DONE at the end!
	"""

	if WHICHSYSTEM == "slurmspinon":
		username = "pavesic"

	elif WHICHSYSTEM == "slurmmaister":
		username = "lukap"

	elif WHICHSYSTEM == "slurmNSC":
		username = "lukap"

	elif WHICHSYSTEM == "slurmvega":
		username = "lukap"



	#PARSE THE QUEUE
	os.system('squeue -u {0} -o "%.200j %.12M" -h > statJobs.txt'.format(username))
	f = open("statJobs.txt", "r")
	queue = [line.rstrip('\n').strip() for line in f]	#strip the newline characters and whitespace
	f.close()

	jobStatuses={}

	#GET JOBS IN QUEUE
	for entry in queue:
		a = re.search("("+ regexName +")" + "\s*(\d?-?\d{,2}:\d{,2}:?\d*)", entry)	#This regex matches the time output in squeue
		if a:
			time = a.group(a.lastindex)
			name = a.group(1)

			if time == "0:00":
				jobStatuses[name] = "Queuing"

			else:
				jobStatuses[name] = "Running"


	#GET THE FINISHED JOBS TOO
	for folder in os.listdir("results/"):
		if os.path.isdir("results/"+folder):
			#if a file called DONE is in the folder, the job is finished
			if "DONE" in os.listdir("results/"+folder):
				jobStatuses[folder] = "Finished"

			#if there is START but no DONE and the job is not in the queue, it has failed
			elif "START" in os.listdir("results/"+folder):
				if not folder in jobStatuses:
					jobStatuses[folder] = "Failed"

	return jobStatuses

#####################################################################################################
#FUNCTIONS FOR SENDING JOBS

def clean(job):
	"""
	Cleans a job with a given job name.
	"""

	WHICHSYSTEM = os.environ["WHICHSYSTEM"]

	if WHICHSYSTEM == "arc":
		jobStatuses = cleanArc(job)

	elif re.match("slurm.*", WHICHSYSTEM):
		jobStatuses = cleanSlurm(job)

def cleanArc(job):
	"""
	Cleans a job using arcclean.
	NOTE: this could be made faster by pasing to arcclean an entire list of failed jobs,
	but it seems to be less reliable.
	"""
	os.system("arcclean {0}".format(job))

def cleanSlurm(job):
	"""
	Cleans a failed job. Removes its directory from results/.
	"""
	os.system("rm -r results/{0}/".format(job))

def run(job):
	"""
	Runs the job in the folder results/jobname.
	This is basically a copy of the sendSlurm() function, just that it executes the script in place instead of sbatch
	"""

	#check if the folder exists and remove it if it does
	if os.path.exists("results/{0}".format(job)):
		#if it exists, the job has failed, remove it:
		os.system("rm -rf results/{0}/".format(job))

	#make an empty folder
	os.mkdir("results/{0}".format(job))

	#get parameters and their values
	paramDict = nameToParamsVals(job, nameFile="nameFile")

	#write an input file and move it into the job folder
	editInputFile(paramDict)
	os.system("mv {0} results/{1}/".format("inputFile", job))

	#copy the SAMPLEscript to the job folder
	os.system("cp SAMPLEscript results/{0}/script".format(job))
	os.system("chmod +x results/{0}/script".format(job))

	#change the current directory to the job folder
	os.chdir("results/{0}".format(job))

	#execute the script
	os.system("./script")

	#change the current directory back
	os.chdir("../..")

	return None

def send(job, cluster_sub_host, scriptname="SAMPLEscript"):
	"""
	Sends a job with a given jobname.
	"""

	WHICHSYSTEM = os.environ["WHICHSYSTEM"]

	if WHICHSYSTEM == "arc":
		jobStatuses = sendArc(job, cluster_sub_host)

	elif re.match("slurm.*", WHICHSYSTEM):
		jobStatuses = sendSlurm(job, scriptname)

	return None

def sendArc(job, cluster_sub_host):
	"""
	Sends a job to maister hpc via arc.
	"""

	#get parameters and their values
	paramDict = nameToParamsVals(job, nameFile="nameFile")

	#write an input file
	editInputFile(paramDict)

	#write sendJob.xrsl
	editSendJobxrsl(job)

	#send job
	#os.system("arcsub -c maister.hpc-rivr.um.si sendjob.xrsl")	#sending to maister
	os.system(f"arcsub -c {cluster_sub_host} sendjob.xrsl")

	return None

def sendSlurm(job, scriptname="SAMPLEscript"):
	"""
	Sends a job to slurm with sbatch.
	scriptname is the name of the script.
	"""

	#check if the folder exists and remove it if it does
	if os.path.exists("results/{0}".format(job)):
		#if it exists, the job has failed, remove it:
		os.system("rm -rf results/{0}/".format(job))

	#make an empty folder
	os.mkdir("results/{0}".format(job))

	#get parameters and their values
	paramDict = nameToParamsVals(job, nameFile="nameFile")

	#write an input file and move it into the job folder
	editInputFile(paramDict)
	os.system("mv {0} results/{1}/".format("inputFile", job))

	#copy the script to the job folder
	os.system(f"cp {scriptname} results/{job}/script")
	os.system(f"chmod +x results/{job}/script")

	batchDict = getBatchParamsNameFile("nameFile")
	#write the batch script
	writeBatchScript(batchDict, job)

	#change the current directory to the job folder
	os.chdir("results/{0}".format(job))
	#sbatch to send job
	os.system("sbatch sendJob".format(job))
	#change the current directory back
	os.chdir("../..")

	return None
