# Please call it "One For All" script
import os
import sys
import re
import pprint
import io
import codecs
import random
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("sql_version", help="Build SQL util this Equator SQL version")
parser.add_argument("build_all_test_files", nargs='?' , type=lambda s: s.lower() in ['true', 'y', 'yes', '1'], help="Create test_executable.sql from all version folder")
parser.add_argument("merge_all_versions", nargs='?' , type=lambda s: s.lower() in ['true', 'y', 'yes', '1'], help="Merge all created SQL executable script ")
args = parser.parse_args()

version = args.sql_version
buildTestScriptBool = args.build_all_test_files
mergeScriptBool = args.merge_all_versions

expectedFileType = ".sql"
executableFileName = "_executable" + expectedFileType
alpTestingPatchFileName = "alp_testing_patch" + expectedFileType

# defaultConfigFilePath = os.path.join(version, "value.txt")
# configFilePath= sys.argv[2] if len(sys.argv) > 2 else defaultConfigFilePath

# ignoredFolderPaths = ["/xxxxxxxxx/"]
mergedFilePath = "merged_sql.txt"
testExecutableFilePath = "test_executable.sql"
mergedExecutableFilePath = "ultimatum_executable.sql"
templateKeyValueFilePath = "value.txt"
ignoredTemplateKeyValueFile = os.path.abspath(os.path.join("template", version, templateKeyValueFilePath))

C1   = '\033[31m' # Red
C2   = '\033[32m' # Green
C3   = '\033[33m' # Yellow
C4   = '\033[34m' # Blue
C5   = '\033[35m' # Magenta
C6   = '\033[36m' # Cyan

W   = '\033[0m'  # white (normal)
BG = '\033[32;5m' # bliking green
BR = '\033[31;5m' # bliking red

colourful = [C3, C4, C5, C6]


def listAllSql(path, endswithFileName):
    print("@@@@ Listing all sorted SQL template by alphabet in path : %s" % path)
    sqlFiles = []
    for root, directories, filenames in os.walk(path):
        for filename in filenames:
            # if any(ext not in root for ext in ignoredFolderPaths):
            if filename.endswith(endswithFileName):
                sqlFiles.append(os.path.join(root, filename))
    if not sqlFiles:
        sys.exit("@@@@ !! Not found file in path : %s" % path)
    return sorted_nicely(sqlFiles)
# path, filename = os.path.split(path)
def cutVersionPrefixKey(path_):
    filename = os.path.basename(path_)
    if filename[0].isdigit():
        versionFilename = filename.split("_")[0]
        return versionFilename
    elif filename.endswith(executableFileName):
        return filename.split("_")[0]
    return path_

def sorted_nicely( l ):
    sortedList = sorted(l, key = cutVersionPrefixKey)
    print(*sortedList, sep="\n")
    return sortedList

def mergeTextFile(sqlFiles, mergedFile):
    # Create file as a temporary
    with io.open(mergedFile, "w", encoding="utf8") as outfile:
        for fname in sqlFiles:
            with io.open(fname) as infile:
                for line in infile:
                    outfile.write(line)

def deleteFile(file):
    if os.path.isfile(file):
        os.remove(file)
    else:
        print(BR +"@@@@ !!! WARNING " + W + " : %s file not found" % file)


def readConfigFile(configFile):
    replacements = {}
    absolutePathConfigFile = os.path.abspath(configFile)
    print("@@@@ Loading replacement key/value file from : %s" % absolutePathConfigFile)
    with io.open(configFile, "r", encoding="utf8") as infile:
        for line in infile:
            (key, val) = line.split("=", 1)
            replacements[key.rstrip()] = codecs.decode(val.rstrip("\n"),"unicode_escape")
    return replacements


def replaceMergedFileWithLoadedKey(mergedFile, replacements, resultFile):
    print("@@@@ Replacing merged template SQL with loaded key/value")
    wordfreq = {}
    with io.open(mergedFile, "r", encoding="utf8") as infile, io.open(resultFile, "w", encoding="utf8") as outfile:
        for line in infile:
            for key, value in replacements.items():

                ##
                pattern = re.compile(r"\.*(#" + key + "#)\.*")
                counted = len(pattern.findall(line))
                if key not in wordfreq:
                    wordfreq[key] = 0
                wordfreq[key] += counted
                ##

                line = line.replace("#" + key + "#", value)
            outfile.write(line)
    print ("@@@@ Summary replaced key : ")
    pprint.pprint(wordfreq, width=1)

def verifyUnusedKeyInResultFile(resultFile):
    pattern = re.compile(r"\.*(#[A-Z_0-9]+#)\.*")
    countLine = 0
    with io.open(resultFile, "r", encoding="utf8") as infile:
        for line in infile:
            countLine += 1
            if pattern.findall(line):
                print (BR +"@@@@ !!! WARNING " + W + ": Found non-replaced key in result file at line %s > %s" % (countLine, pattern.findall(line)))

def listDirNames(path):
    return [dI for dI in os.listdir(path) if os.path.isdir(os.path.join(path,dI))]

def buildTestScript(versionDirlist):
    print("@@@@ Building test script from all versions")
    deleteFile(testExecutableFilePath)
    allTestSqlFiles = []
    for versionDir in versionDirlist:
        if (versionDir > version):
            break
        testFailPath = os.path.join("template", versionDir, "test_data_scripts")
        if not os.path.exists(testFailPath):
            print("@@@@ Skip test patch for version %s " % versionDir)
            continue
        testSqlFiles = listAllSql(testFailPath, alpTestingPatchFileName)
        allTestSqlFiles = allTestSqlFiles + testSqlFiles
    mergeTextFile(allTestSqlFiles, testExecutableFilePath)


##############################################################################################
# Example for run on local :$ python build_sql.py 2.0 yes yes

def main():
    versionDirlist =listDirNames("template")
    for versionDir in versionDirlist:
        col = random.choice(colourful)
        resultFilePath = versionDir + executableFileName
        if (versionDir > version):
            break
        print(col + "################################## Start build version %s ##################################" % versionDir + W)
        sqlPath = os.path.join("template", versionDir, "sql_scripts")
        replaceFilePath = os.path.abspath(os.path.join("template", versionDir, templateKeyValueFilePath))
        print("@@@@ Try to delete existing result file : %s" % resultFilePath)
        deleteFile(resultFilePath)
        sqlFiles = listAllSql(sqlPath, expectedFileType)
        replacements = readConfigFile(replaceFilePath)
        mergeTextFile(sqlFiles, mergedFilePath)
        replaceMergedFileWithLoadedKey(mergedFilePath, replacements, resultFilePath)
        deleteFile(mergedFilePath)
        verifyUnusedKeyInResultFile(resultFilePath)
        print("@@@@ Complete build SQL : ["+ BG +"%s" % resultFilePath + W + "]")
        print(col + "################################## Finish build version %s ##################################" % versionDir + W)

    if buildTestScriptBool:
        col = random.choice(colourful)
        print(col + "################################## Start build test data script ##################################" + W)
        buildTestScript(versionDirlist)
        print("@@@@ Complete build SQL :["+ BG +"%s" % testExecutableFilePath + W + "]")
        print(col + "################################## Finish build test data script ##################################" + W)

    if mergeScriptBool:
        print("@@@@ Building Ultimatum SQL")
        deleteFile(mergedExecutableFilePath)
        sqlExecuteFiles = listAllSql(os.getcwd(), executableFileName)
        mergeTextFile(sqlExecuteFiles, mergedExecutableFilePath)
        print("@@@@ Complete build SQL :["+ BG +"%s" % mergedExecutableFilePath + W + "]")

if __name__ == "__main__":
    main()
