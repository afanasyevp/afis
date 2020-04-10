#!/home/pafanasyev/software/anaconda3/bin/python 

ver=200410

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

def extract_OpticsGroup(micrograph, OpticsGroup):
    '''
    finds and returns opticsgroup for a given micrograph
    '''
    result=OpticsGroup[extract_moviename(micrograph)]
    return result

def star_analyze(star_filename):
    '''
    creates dicrionaries from the star files.
    assumes for now version 3.1
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
        star_line=line.split()
        if len(star_line) > 0:
            if line[:10] == "# version ":
                OpticsHeader['# version']=star_line[2]
            elif line[:5] == "loop_": 
                continue
            elif line[:11]=="data_optics":
                #print("Data_optics found!")
                continue
            elif line[:4] == "_rln":
                OpticsHeader[star_line[0]]=int(star_line[1][1:])
            elif line[:11]=="opticsGroup":
                OpticsGroupData[star_line[0]]=line[:-1]
            elif line[:5] == "data_":
                data_type=line[:-1].split("_")[1]
                #print("Data_%s found!" %data_type)
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
                continue
                #print("Data_%s found!" %data_type)
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
    data_merged={}
    header_merged = {**header_1, **header_2}
    indexes_of_values_to_add=[]
    values_to_add='    '
    for key, value in header_merged.items():
        if key in header_1 and key in header_2:
            if value == header_1[key]:
                header_merged[key] = header_1[key]
            else:
                   print("WARNING!!! Optic header values of the micrographs- and particles- star files do not match! The new star file might be messed up!!!")
        else:
            indexes_of_values_to_add.append(int(value))
    
    for i in indexes_of_values_to_add:
        values_to_add=values_to_add+(data_2['opticsGroup1'].split()[i-1]+ "    ") 
    
    for k,v in data_1.items():
        data_merged[k]=v+values_to_add
    #print("header_merged", header_merged)
    #print("header_input", header_1)
    return header_merged, data_merged



def micrographs_write_optics(OpticsFileName, MainFileName, Output):
    '''
    reads in the a file with optics and without; writes out a new star-file.
    requires star_analyze
    '''
    OpticsFile_MainHeader, OpticsGroupData, OpticsHeader, MoviesData, StarFileType = star_analyze(OpticsFileName)
    MainFile_MainHeader, Main_OpticsGroupData, Main_OpticsHeader, MainFile_Data, MainFile_StarFileType = star_analyze(MainFileName)

    ##create a dictionary-helper to identify micrographs's group
    _rlnOpticsGroupInMovies_index=OpticsHeader['_rlnOpticsGroup']
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
            MainFile_Data[k][_rlnOpticsGroupInMain_index-1]=OpticsGroup[extract_moviename(k)]
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
 - Download and install the latest Anaconda with python 3.7
 - Modify the first line of the script to change the location of the python execultable to 
the installed Anaconda's python 

[version %s]
Written and tested in python3.7

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
    print("Example: optics_add.py --mov ./movies.star --microgr ./micrographs_ctf.star --o microghraphs_ctf_optics.star")
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
