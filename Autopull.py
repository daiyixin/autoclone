#!/usr/bin/python3

import sys
import subprocess
from os import path
from os import chdir
from enum import IntEnum



################################################################################
#SECTION: global constants.

STR_HELP_REQUIREMENTS = """
External software dependencies:
Required: python 3.x
Optional: git, subversion, mercurial, 7zip
"""

STR_HELP_USAGE = """
Autopull has 4 operation modes: update, add, edit, and remove.

Syntax:
<x> represents a single value field where x is the name of the parameter.
<{x, y, etc}> means a ranged field where x, y, and etc are parameter options to choose from.

Structure of update command (4 types):
To update everything:
1) autopull
2) autopull <update alias>

To update a single subdirectory:
3) autopull <update alias> <subdir>

To update a single repository:
4) autopull <update alias> <subdir> <repo name>

Structure of add command:
autopull <add alias> <{git alias, subversion alias, mercurial alias}> <url> <subdir> <repo name> <{no, 7z}>

Structure of edit command:
autopull <edit alias>

Structure of remove command:
autopull <remove alias> <subdir> <repo name>

Additionally to the main operations there is a command loop feature.
The command loop allows you to run sequential commands without reinvoking Autopull.

To start a command loop (3 options):
1) autopull <loop alias>

With an initial command:
2) autopull <command> <loop alias>
3) autopull <loop alias> <command>

You'll notice that some parameters require an alias.
All alias have no case sensitivity and can be found by passing \"alias\" or \"aliases\" as the first argument when invoking autopull or by reading the code.
Search (ctrl+f) for \"argument aliases\" to jump to them.
They are inside lists that are part of the code.
"""

STR_HELP_DATABASE = """
Records in the repo_list.txt flat file database are structured as follows where all fields are tab separated:
<version controller>\t<url>\t<subdirectory>\t<repo name>\t<compression>
"""

STR_TRIM_DEBUG = "Trimmed {} from sys args:\n{}"
STR_INVALID_ARG = "Invalid command given. Invoke with \"help\" as the first argument to be given usage instructions."
STR_INVALID_LOOP = "There can only be one command loop running, but the expected command will be processed."

STR_LIST_FILE = "repo_list.txt"

LST_HELP_ALIAS = ["h", "help"]
LST_ALIAS_ALIAS = ["alias", "aliases"]

LST_LOOP_ALIAS = ["l", "loop"]
LST_QUIT_ALIAS = ["q", "quit", "exit", "done"]

LST_UPDATE_ALIAS = ["u", "update"]
LST_ADD_ALIAS = ["a", "add", "append"]
LST_EDIT_ALIAS = ["e", "edit"]
LST_REMOVE_ALIAS = ["r", "remove", "delete"]

LST_GIT_ALIAS = ["g", "git"]
LST_SUBVERSION_ALIAS = ["s", "svn", "subversion"]
LST_MERCURIAL_ALIAS = ["m", "mercurial", "hg", "h"]

class Record(IntEnum):
	VCS = 0
	URL = 1
	SUBDIR = 2
	NAME = 3
	ZIP = 4



################################################################################
#SECTION: global variables.

fileRepoList = None



################################################################################
#SECTION: alias utilities.

def alias_list_has(lstList, strArg): #SUMMARY: check if an arg exists in an alias list plainly or with single or double dashes.
	blnFound = False

	for strString in lstList:
		if (
			strString.lower() == strArg.lower() or
			"-" + strString.lower() == strArg.lower() or
			"--" + strString.lower() == strArg.lower()
		):
			blnFound = True
			break

	return blnFound



def print_alias_list(strHeading, lstList): #SUMMARY: prints all combinations of an alias on a single line.
	STR_TEMPLATE = "{arg}\t\t-{arg}\t\t--{arg}"

	print(strHeading)

	for strString in lstList:
		print(STR_TEMPLATE.format(arg = strString.lower()))



################################################################################
#SECTION: data validation utilities.

def validate_repo_list(): #SUMMARY: create an empty repo list if none exists.
	blnValid = False

	if not path.exists(STR_LIST_FILE):
		#print("Repo list validation failed.") #FOR DEBUG: notify if repo list not found.
		open(STR_LIST_FILE, "w").close()

	else:
		#print("Repo list validation sucessful.") #FOR DEBUG: notify if repo list was found.
		blnValid = True

	return blnValid



def get_matching_records(strSubdir = None, strName = None): #SUMMARY: check if a record with matching values exists in the repo list.
	lstFound = []

	for strRecord in fileRepoList:
		lstRecord = strRecord.split("\t")

		#if a name match is required.
		if (
			strName != None and
			lstRecord[Record.NAME] == strName and
			lstRecord[Record.SUBDIR] == strSubdir
		):
			print(lstRecord) #FOR DEBUG: display every matching record.
			lstFound.append(lstRecord)

		#if only a subdir match is required.
		elif lstRecord[Record.SUBDIR] == strSubdir:
			print(lstRecord) #FOR DEBUG: display every matching record.
			lstFound.append(lstRecord)

		#if theres no match.
		else:
			pass

	print(len(lstFound + "")) #FOR DEBUG: display the number of found matches.

	return lstFound



def find_duplicate_records(strURL, strSubdir, strName): #SUMMARY: null
	lstMatches = []
	#pass #TODO
	return lstMatches



def validate_local_repo(strSubdir, strName): #SUMMARY: find and remove identically named subdir.
	STR_REPO_PATH = "{}/{}".format(strSubdir, strName)

	if path.exists(STR_REPO_PATH) or path.isfile(STR_REPO_PATH):
		chdir(strSubdir)
		subprocess.run(["rm", "-rf", strName])
		chdir("..")



def validate_remote_repo(strVCS, strURL): #SUMMARY: check if the remote repository exists.
	blnValid = False
	cprResult = None

	#try contacting remote repo.
	if strVCS == "git":
		cprResult = subprocess.run(["git", "ls-remote", strURL, "-q"])

	elif strVCS == "svn":
		cprResult = subprocess.run([])

	elif strVCS == "hg":
		cprResult = subprocess.run([])

	#determine validity from exit code.
	if cprResult.returncode == 0:
		blnValid = True

	print("Remote validation returned " + str(cprResult.returncode) + " ({})".format(blnValid))
	return blnValid



################################################################################
#SECTION: data transform utilities.

def compress_local_repo(strSubdir, strName, strZip): #SUMMARY: compress a local repo if required.
	if strZip == "7z":
		chdir(strSubdir)
		subprocess.run(["7z", "a", "-t7z", "-m0=lzma2", "-mx=9", "-mfb=64", "-md=32m", "-ms=on", "-mhe=on", strName, ".7z ", "-y", "-bsp0", "-bso0", strName])
		subprocess.run(["rm", "-rf", strName])
		chdir("..")

	else:
		print("Unknown zip procedure " + strZip)



def download_remote_repo(lstParams): #SUMMARY: download the repository.
#NOTE: lstParams = [string vcs, string url, string subdir, string name, string zip]
	if (
		validate_remote_repo(lstParams[Record.VCS], lstParams[Record.URL])
	):
		print("Record validation successful.") #FOR DEBUG: notify record validation success.
		validate_local_repo(lstParams[Record.SUBDIR], lstParams[Record.NAME])

		#do the actual download.
		if lstParams[Record.VCS] == "git":
			subprocess.run(["git", "clone", lstParams[Record.URL], "{}/{}".format(lstParams[Record.SUBDIR], lstParams[Record.NAME])])

		elif lstParams[Record.VCS] == "svn":
			subprocess.run(["svn", "checkout", lstParams[Record.URL], "{}/{}".format(lstParams[Record.SUBDIR], lstParams[Record.NAME])])

		elif lstParams[Record.VCS] == "hg":
			subprocess.run("hg", "clone", lstParams[Record.URL], lstParams[Record.NAME])

		#compress for storage.
		if lstParams[Record.ZIP] != "none":
			compress_local_repo(lstParams[Record.SUBDIR], lstParams[Record.NAME], lstParams[Record.ZIP])

	else:
		print("Record validation failed.") #FOR DEBUG: notify record validation failure.



################################################################################
#SECTION: operations.

def update_operation(lstParams = []): #SUMMARY: update a quantity of local backups.
#NOTE: lstParams = [string subdir, string name]
	global fileRepoList
	global STR_LIST_FILE

	lstValidrecords = []

	print("Update operation selected.") #FOR DEBUG: notify that update operation started.
	if not validate_repo_list():
		return

	fileRepoList = open(STR_LIST_FILE, "r")

	#update a specific repo.
	if len(lstParams) > 1:
		print("...Updating with subdir and name params.") #FOR DEBUG: notify update with subdir and name params.
		lstValidrecords = get_matching_records(lstParams[0], lstParams[1])

	#update a subdir.
	elif len(lstParams) > 0:
		print("...Updating with subdir param.") #FOR DEBUG: notify update with only subdir param.
		lstValidrecords = get_matching_records(lstParams[0])

	#update everything.
	else:
		print("...Updating with no params.") #FOR DEBUG: notify update with no params.
		for strRecord in fileRepoList:
			lstValidrecords.append(strRecord.split("\t"))

	#validate the target and perform the operation.
	for lstRecord in lstValidrecords:
		download_remote_repo(lstRecord)

	fileRepoList.close()



def add_operation(lstParams): #SUMMARY: add a new record to the bottom of the repo list.
#NOTE: lstParams = [string vcs, string url, string subdir, string name, string zip]
	global fileRepoList

	print("Add operation selected.") #FOR DEBUG
	if not validate_repo_list():
		return

	fileRepoList = open(STR_LIST_FILE, "a")

	#search for duplicates.
	lstDuplRecords = find_duplicate_records(lstParams[Record.URL], lstParams[Record.SUBDIR], lstParams[Record.NAME])
	if len(lstDuplRecords) > 0:
		print("Duplicate records were found:", lstDuplRecords)

	else:
		strRecord = "\n" + lstParams[Record.VCS]
		for strString in lstParams[1:]:
			strRecord += "\t{}".format(strString)

		#TODO: disallow periods in subdir and name field.
		fileRepoList.write(strRecord)
		download_remote_repo(lstParams)

	fileRepoList.close()



def edit_operation(lstParams): #SUMMARY: modify a record in the repo list.
#NOTE: lstParams = []
	global fileRepoList
	global STR_LIST_FILE

	print("Edit operation selected.") #FOR DEBUG
	if not validate_repo_list():
		return

	fileRepoList = open(STR_LIST_FILE, "r")

	#TODO
	#find the requested repo.
	#write in the changed record.

	fileRepoList.close()



def remove_operation(lstParams): #SUMMARY: search the repo list and delete a record.
#NOTE: lstParams = []
	global fileRepoList
	global STR_LIST_FILE

	print("Remove operation selected.") #FOR DEBUG
	if not validate_repo_list():
		return

	fileRepoList = open(STR_LIST_FILE, "r")

	#TODO
	#find the requested repo.
	#remove it and the empty line.

	fileRepoList.close()



def command_loop(lstParams = []): #SUMMARY: start a loop that can receive multiple commands.
#NOTE: lstParams = []
	print("Command loop selected.") #FOR DEBUG

	lstCmd = lstParams
	blnDone = False

	while not blnDone:
		#get a command if there is none.
		if len(lstCmd) == 0:
			lstCmd = input("Awaiting command:").split("\t")

		#print help.
		elif alias_list_has(LST_HELP_ALIAS, lstCmd[0]):
			pass #print through the help pages based on sys args.
			lstCmd.clear()

		#print all alias.
		elif alias_list_has(LST_ALIAS_ALIAS, lstCmd[0]):
			pass #print through the aliases based on sys args.
			lstCmd.clear()

		#deny a new pre-command loop invocation.
		elif alias_list_has(LST_LOOP_ALIAS, lstCmd[0]):
			print(STR_INVALID_LOOP)
			lstCmd = lstCmd[1:]

		#deny a new post-command loop invocation.
		elif alias_list_has(LST_LOOP_ALIAS, lstCmd[-1]):
			print(STR_INVALID_LOOP)
			lstCmd = lstCmd[:-1]

		#quit the command loop back to the terminal.
		elif alias_list_has(LST_QUIT_ALIAS, lstCmd[0]):
			blnDone = True

		#do an update operation.
		elif alias_list_has(LST_UPDATE_ALIAS, lstCmd[0]):
			update_operation(lstCmd)
			lstCmd.clear()

		#do an add operation.
		elif alias_list_has(LST_ADD_ALIAS, lstCmd[0]):
			add_operation(lstCmd)
			lstCmd.clear()

		#do an edit operation.
		elif alias_list_has(LST_EDIT_ALIAS, lstCmd[0]):
			edit_operation(lstCmd)
			lstCmd.clear()

		#do an remove operation.
		elif alias_list_has(LST_REMOVE_ALIAS, lstCmd[0]):
			remove_operation(lstCmd)
			lstCmd.clear()

		#handle an invalid command.
		else:
			print(lstCmd) #FOR DEBUG
			print(STR_INVALID_ARG)
			lstCmd.clear()



################################################################################
#SECTION: entry point.

if __name__ == "__main__":
	#trim invocation from args.
	sys.argv = sys.argv[1:]
	#print(STR_TRIM_DEBUG.format("invocation", sys.argv)) #FOR DEBUG

	#check if the user gave any args.
	if len(sys.argv) == 0:
		#print("No sys args given.") #FOR DEBUG: notify no sys args given.
		update_operation()

	else:
		#check if the user asked for instructions.
		if alias_list_has(LST_HELP_ALIAS, sys.argv[0]):
			pass #print through the help pages based on sys args.

		#check if the user asked for aliases.
		elif alias_list_has(LST_ALIAS_ALIAS, sys.argv[0]):
			pass #print through the aliases based on sys args.

		#check if the user wants to start a command loop.
		elif alias_list_has(LST_LOOP_ALIAS, sys.argv[0]):
			sys.argv = sys.argv[1:]
			print(STR_TRIM_DEBUG.format("pre-command loop", sys.argv)) #FOR DEBUG: display modified sys arg set.
			command_loop(sys.argv)

		elif alias_list_has(LST_LOOP_ALIAS, sys.argv[-1]):
			sys.argv = sys.argv[:-1]
			print(STR_TRIM_DEBUG.format("post-command loop", sys.argv)) #FOR DEBUG: display modified sys arg set.
			command_loop(sys.argv)

		#check if the user wants an update operation.
		elif alias_list_has(LST_UPDATE_ALIAS, sys.argv[0]):
			sys.argv = sys.argv[1:]
			print(STR_TRIM_DEBUG.format("update alias", sys.argv)) #FOR DEBUG: display modified sys arg set.
			update_operation(sys.argv)

		#check if the user wants an add operation.
		elif alias_list_has(LST_ADD_ALIAS, sys.argv[0]):
			sys.argv = sys.argv[1:]
			print(STR_TRIM_DEBUG.format("add alias", sys.argv)) #FOR DEBUG: display modified sys arg set.
			add_operation(sys.argv)

		#check if the user wants an edit operation.
		elif alias_list_has(LST_EDIT_ALIAS, sys.argv[0]):
			sys.argv = sys.argv[1:]
			print(STR_TRIM_DEBUG.format("edit alias", sys.argv)) #FOR DEBUG: display modified sys arg set.
			edit_operation(sys.argv)

		#check if the user wants an remove operation.
		elif alias_list_has(LST_REMOVE_ALIAS, sys.argv[0]):
			sys.argv = sys.argv[1:]
			print(STR_TRIM_DEBUG.format("remove alias", sys.argv)) #FOR DEBUG: display modified sys arg set.
			remove_operation(sys.argv)

		#the user gave an invalid arg.
		else:
			print(STR_INVALID_ARG)

	sys.exit(0)