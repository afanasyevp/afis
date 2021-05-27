#!/Applications/anaconda/bin/python 

ver=210108

import sys
import os
import argparse
import re

def extract_moviename(path): 
    '''Extracts filename of a given path without extension:
input: ./movies/FoilHole_14476491_Data_14478410_14478412_20191214_161005_fractions.tiff
output: FoilHole_14476491_Data_14478410_14478412_20191214_161005_fractions
    assumes only one "." in the filename (in front of the extension)
    ''' 
    filename = re.search(r'(\S+\/)(\S+)', path) 
    if filename: 
        return (filename.group(2)).split(".")[0]
    else: 
        return path 

def star_analyze(star_filename):
    '''
    creates dicrionaries from the star files: 
        OpticsHeader: everything starting with _rlnXXXX, corresponding to the data_optics section
        "# version 30001
        data_optics
        loop_
        _rlnOpticsGroupName #1" etc

        OpticsGroupData:  all the data after the previous section like:  
        "opticsGroup1           1     0.43   300     2.7     0.1"
        
        MainHeader:  everything starting with _rlnXXXX, corresponding to the data_movies or data_particles section
        "# version 30001
        data_particles
        loop_
        _rlnCoordinateX #1"
        
        StarData:  main data (alignments data for particles.star) after the previous section like:   
        "mov1.tiff 25" (movies.star) or "3.43 6.2 0.1 10 8.2 000001@Extract/job044/Micro/mov1.mrcs MotionCorr/job034 /Micro/mov1.mrc 1 0.1 6.1 6.4 44.8 0.0 1.0 0.0 " (particles.star)
    '''
    ## optics header dictionaries 
    OpticsHeader={}    
    OpticsGroupData={} 
    ## main header dictionaries
    MainHeader={}  
    StarData={}    
    with open(star_filename, 'r') as star_file: 
        lines=star_file.readlines()
    ## create OpticsHeader and OpticGroupData dictionary 
    for line in lines[:]:
        #print(line)
        star_line=line.split()
        #print("splitline:", star_line)
        if len(star_line) > 0:
            if line[:10] == "# version ":
                OpticsHeader['# version']=star_line[2]
                #print("version:", OpticsHeader['# version'])
            elif line[:5] == "loop_": 
                continue
            elif line[:11]=="data_optics":
                #print("Data_optics found!")
                continue
            elif line[:4] == "_rln":
                OpticsHeader[star_line[0]]=int(star_line[1][1:])
            elif line[:11]=="opticsGroup":
                OpticsGroupData[star_line[0]]=line[:-1]
                #print(OpticsGroupData)
            elif line[:5] == "data_":
                data_type=line[:-1].split("_")[1]
                #print("Data_%s found!" %data_type)
                lines.pop(0)
                break
            else:
                continue
        lines.pop(0)
    if '# version' not in OpticsHeader.keys():
        OpticsHeader['# version']="unknown"
    ## create MainHeader dictionary with the main Header
    for line in lines[:]:
        star_line=line.split()
        if len(star_line) > 0:
            if line[:10] == "# version ":
                MainHeader['# version']=star_line[2]
            elif line[:5] == "data_":
                data_type=line[:-1].split("_")[1]
                #print("Data_%s found!" %data_type)
                continue
            elif line[:5] == "loop_": 
                continue
            elif line[:4] == "_rln":
                MainHeader[star_line[0]]=int(star_line[1][1:])
                if line[:24] == "_rlnMicrographMovieName ":
                    _rlnMicrographMovieName_index=int(star_line[-1].split("#")[-1])
                    #print("_rlnMicrographMovieName_index", star_line[-1].split("#")[-1])
                elif line[:19] == "_rlnMicrographName ":
                    _rlnMicrographName_index=int(star_line[-1].split("#")[-1])
                    #print("_rlnMicrographName_index", star_line[-1].split("#")[-1])
                elif line[:14] == "_rlnImageName ":
                    _rlnImageName_index=int(star_line[-1].split("#")[-1])
                    #print("_rlnImageName_index", star_line[-1].split("#")[-1])
            else:
                ## create main StarData dictionary, where the key is the main header
                ## identifier is  micrograph/movie/particle name
                if data_type == "micrographs":
                    StarData[star_line[(_rlnMicrographName_index-1)]]=star_line
                elif data_type == "movies":
                    StarData[star_line[(_rlnMicrographMovieName_index-1)]]=star_line
                elif data_type == "particles":
                    StarData[star_line[(_rlnImageName_index-1)]]=star_line 
                    continue
                else:
                    print("ERROR: no data type found!")
                    sys.exit(2)
                #print("break at:", line)
                #break
        lines.pop(0)
    if '# version' not in MainHeader.keys():
        MainHeader['# version']="unknown"
    StarFileType=data_type     
    #print("MainHeader: ", MainHeader, "\n")
    #print("StarData dictionary: ", StarData, "\n")
    #print("OpticsGroupData", OpticsGroupData, "\n")
    #print("OpticsHeader: ", OpticsHeader, "\n") 
    return MainHeader, OpticsGroupData, OpticsHeader, StarData, StarFileType

def merge_optics_headers(header_1, header_2, data_1, data_2):
    '''
    Merges optics and data headers:
    header_1: optics header from the movies (micrographs) file
    header_2: particles optics-header from the particles file
    data_1: optics group-data from the movies (micrographs) file
    data_2: particles optics group-data (one line) from the particles file
    '''
    data_merged={}
    header_merged=header_1  # the optics header is taken from particles.star file 
    #checks if the optics header movies.star contains anything extra to be included
    new_indexes_of_extra_values=[]
    old_indexes_of_extra_values=[]
    extra_values_to_add=" "
    
    for key in header_2:
        if key not in header_1:
            print("WARNING!!!!! Found an extra column in the particles-file, missing in micrographs-file: ", key, "\n This column and the corresponding values will be included in the output file" )
            header_merged[key]=len(header_merged) #append the missing(extra) column, found in the movies file and missing in the particles file
            new_indexes_of_extra_values.append(header_merged[key])
            old_indexes_of_extra_values.append(header_2[key])
    #print("new_indexes_of_extra_values", new_indexes_of_extra_values)
    #print("old_indexes_of_extra_values", old_indexes_of_extra_values)
    #print("header_merged", header_merged)
    if len(data_2)==1: 
        #convert data_2 dictionary with a sigle entry to a list and picking the right values to include into the new data_merged:
        data_2_value=str(*data_2.values()).split()
        for i in old_indexes_of_extra_values:
            extra_values_to_add=extra_values_to_add+str(data_2_value[i-1])+"   "
    else:
        print("ERROR: particles.star file already contains multiple OpticsGroups or none. You might consider deleting them manually and leaving a single one")
        sys.exit(2) 
    #print("extra_values_to_add", extra_values_to_add)
    
    #actual merging of the optics data:
    for k,v in data_1.items():
        data_merged[k]=v+extra_values_to_add
    return header_merged, data_merged


def micrographs_write_optics(OpticsFileName, MainFileName, Output):
    '''
    reads in the a file with optics and without; writes out a new star-file.
    requires star_analyze
    '''

    print("working on %s file" % OpticsFileName, "\n") 
    OpticsFile_MainHeader, OpticsGroupData, OpticsHeader, MoviesData, StarFileType = star_analyze(OpticsFileName)
    print("working on %s file" % MainFileName, "\n")
    MainFile_MainHeader, Main_OpticsGroupData, Main_OpticsHeader, MainFile_Data, MainFile_StarFileType = star_analyze(MainFileName)
    ##create a dictionary-helper to identify micrographs's group
    _rlnOpticsGroupInMovies_index=OpticsFile_MainHeader['_rlnOpticsGroup']
    _rlnOpticsGroupInMain_index=MainFile_MainHeader['_rlnOpticsGroup']
    OpticsGroup={}
    for k,v in MoviesData.items():
        OpticsGroup[extract_moviename(k)]=v[_rlnOpticsGroupInMovies_index-1]
    ## Modify MainFile_Data dictionary with modified Optics groups
    #print(MainFile_StarFileType)
    OpticsHeader_output=OpticsHeader
    OpticsGroupData_output=OpticsGroupData
    if MainFile_StarFileType=="particles":
        OpticsHeader_output, OpticsGroupData_output = merge_optics_headers(OpticsHeader, Main_OpticsHeader, OpticsGroupData, Main_OpticsGroupData)
    with open(Output, "w") as outputFile:

        outputFile.write('''
# version %s
data_optics
loop_ 
''' %OpticsHeader['# version'])
        OpticsHeader_output.pop("# version")
        #print(OpticsHeader_output.items())
        for k, v in sorted(OpticsHeader_output.items(), key=lambda item: item[1]):
            outputFile.write("%s #%s \n" %(k, v))
        for k, v in sorted(OpticsGroupData_output.items(), key=lambda item: item[1][1]):
            outputFile.write("%s\n" %v) 
        outputFile.write('''
# version %s
data_%s
loop_ 
''' %(Main_OpticsHeader['# version'],  MainFile_StarFileType))
        MainFile_MainHeader.pop("# version")
        for k, v in sorted(MainFile_MainHeader.items(), key=lambda item: item[1]):
            outputFile.write("%s #%s \n" %(k, v))
        for k,v in MainFile_Data.items():
            try: 
                MainFile_Data[k][_rlnOpticsGroupInMain_index-1]=OpticsGroup[extract_moviename(k)]
            except KeyError:
                print("WARNING!!!! %s movie is not found in the %s file and will be skipped! For this micrograph opticsGroup will not be modified! "%(extract_moviename(k), OpticsFileName)) 
            for item in v: 
                outputFile.write("%s " %item)
            outputFile.write("\n")
        outputFile.write("\n")
        
    
def main():
    output_text='''
========================================= optics_add.py ==========================================
optics_add.py modifies the micrographs_ctf.star file by assigning each micrograph
to its opticsGroup. 
Note:
 - The input mmovies.star file must contain optics groups (please run optics_split)
 - The program works with files from Relion 3.1 version
 - Movie-names cannot contain more than one "." in filename (only in front of the file extension)
 - In case --part option is used, assumed only only one optics group in the particle.star file
 Only particles before CTF-refinement can be used.
How to install and run:   
 - Download and install the latest Anaconda with python 3.6 or later
 - Modify the first line of the script to change the location of the python execultable to 
the installed Anaconda's python 
[version %s]
Written and tested in python3.6
Pavel Afanasyev
https://github.com/afanasyevp/afis/
==================================================================================================
''' % ver 

    parser = argparse.ArgumentParser(description="")
    add=parser.add_argument
    add('--mov',  help="movies.star file with optics group")
    add('--micro', help="micrographs_ctf.star file without optics groups")
    add('--part', help="particles.star file without optics groups")
    add('--o', default="", help="Output star file. If empty no file generated generated.")
    args = parser.parse_args()
    print(output_text)
    parser.print_help()
    print("Example: optics_add.py --mov ./movies.star --micro ./micrographs_ctf.star --o microghraphs_ctf_optics.star")
    print(" ")
    #print(args.mov)
    if len(sys.argv) == 1:
        #parser.print_help()
        sys.exit(2)
    if not args.mov:
        print("ERROR! No proper input is given.")
        #parser.print_help()
        sys.exit(2)
    else:
        movies_filename=str(args.mov) 
    if not args.micro:
            if not  args.part:
                print("ERROR! No proper input is given.")
                sys.exit(2)
    if args.micro:
        star_filename=str(args.micro)
    if args.part:
        star_filename=str(args.part)
    if not args.o:
        print("No output file given. No star file will be saved.")
    
    micrographs_write_optics(movies_filename, star_filename, str(args.o))
        
    print("\nThe program finished successfully. Please critically check the results in the %s file." % args.o)
if __name__ == '__main__':
    main()
