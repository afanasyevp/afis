#!/home/pafanasyev/software/anaconda3/bin/python

ver=200410


import sys
import os
import matplotlib.pyplot as plt
import argparse
import xml.etree.ElementTree as ET
import glob
import numpy as np
from xml.dom import minidom
from sklearn.cluster import KMeans

#### Parser of the FEI .xml file    
    
def get_files(directory, movietype):
    xmlfiles=glob.glob("%s*.xml"% directory)
    #print (xmlfiles)
    moviefiles=[]
    if movietype == "mrc":
        moviefiles =glob.glob("%s*.mrc"%directory)
    elif movietype == "mrcs":
        moviefiles=glob.glob("%s*.mrcs"%directory)
    elif movietype == "tif":
        moviefiles=glob.glob("%s*.tif"%directory)                                                               
    elif movietype == "tiff":
        moviefiles=glob.glob("%s*.tiff"%directory)
    else:
        print("ERROR: the input movie files are %s ;"%movietype, " has to be mrc, mrcs, tiff or tif")
    if len(xmlfiles) != len(moviefiles):
        print ("Warning!!! The number of the .mrc files is different from the number of .xml files")
        for xmlfile in xmlfiles:
            moviefiles.append("%s_fractions.tiff"% xmlfile[:-4])
    return xmlfiles, moviefiles
    

def get_beamShiftArray(xmlfiles, xmlpath):
    #print(xmlpath)
    print("Reading beam shifts from the .xml files... ")
    beamShifts = []
    for index, xmlfile in enumerate(xmlfiles):
        if index % 300 ==0:  print(" Working on %s file...     Progress: %d %% " %(xmlfile, 100*index/len(xmlfiles)))
        xmldoc = minidom.parse("%s" %xmlfile)
        beamshift_items = xmldoc.getElementsByTagName("BeamShift")[0]
        shiftx = beamshift_items.getElementsByTagName("a:_x")
        shifty = beamshift_items.getElementsByTagName("a:_y")
        beamShifts.append([float(shiftx[0].childNodes[0].nodeValue),float(shifty[0].childNodes[0].nodeValue)])
    beamShiftArray = np.array(beamShifts)
    return beamShiftArray

def elbowMethod(maxClusters, inputArray, maxIter, nInit):
    wcss = []
    print("Elbow method is running. Please check the popping-up window ")  
    for i in range(1, maxClusters):
        kmeans = KMeans(n_clusters=i, init='k-means++', max_iter=maxIter, n_init=nInit, random_state=0)
        kmeans.fit(inputArray)
        wcss.append(kmeans.inertia_)
    plt.title('Elbow Method')
    plt.xlabel('Number of clusters')
    plt.ylabel('WCSS')
    plt.plot(range(1, maxClusters), wcss)
    plt.show()

def kmeansClustering(nClusters, inputArray, maxIter, nInit):
    kmeans = KMeans(n_clusters=nClusters, init='k-means++', max_iter=maxIter, n_init=nInit, random_state=0)
    #print("inputArray:",inputArray)
    pred_y = kmeans.fit_predict(inputArray)
    print("K-means clustering is running. Please check the popping-up window ")
    plt.title('Beam-shifts distribution clustering')
    plt.xlabel('Beam-shift X')
    plt.ylabel('Beam-shift Y')
    plt.scatter(inputArray[:, 0], inputArray[:, 1], s=2)
    plt.scatter(kmeans.cluster_centers_[:, 0], kmeans.cluster_centers_[:,1], s=30, c='red')
    plt.show()
    return pred_y

def saveClusteredShifts(fileName, inputArray, clusterIDs):
    clustered_array = np.append(inputArray, np.reshape(np.array(clusterIDs), (-1, 1)), axis=1)
    np.savetxt(fileName, clustered_array, delimiter=',', header="beamShiftX, beamShiftY, clusterNr")


def saveStarFile(starFileName, movieFileNames, pred_y, pxl_size, kev, cs, amp_con, clusters):
    
    with open(starFileName, 'w') as starFile:
        starFile.write('''
# version 30001


data_optics

loop_
_rlnOpticsGroupName #1 
_rlnOpticsGroup #2 
_rlnMicrographOriginalPixelSize #3 
_rlnVoltage #4 
_rlnSphericalAberration #5 
_rlnAmplitudeContrast #6 

''')
        
        for i in range(1,clusters+1):
            starFile.write('''opticsGroup%s            %s     %s   %s     %s     %s
'''%(i, i, pxl_size, kev, cs, amp_con))
        starFile.write('''

data_movies

loop_
_rlnMicrographMovieName #1 
_rlnOpticsGroup #2 
''')
            
        for movieFileName, pred_y_val in zip(movieFileNames, pred_y):
            starFile.write("%s %d\n" % (movieFileName, pred_y_val+1))
        starFile.write("\n")
    
def main():
    output_text='''

========================================= optics_split.py =======================================
optics_split.py modifies the movies.star file by assigning each movie to its opticsGroup. 
This is done by clustering beam-shifts extracted from xml files into beam-shift classes.

Assumptions:
 - Please run the program before importing your data into relion
 - all as the corresponding .xml files are in the same folder as the movie-files
 - the program gives an output for the Relion 3.1 version
 
How to install and run:   
 - Download and install the latest Anaconda with python 3.7
 - Modify the first line of the script to change the location of the python execultable to 
the installed Anaconda's python 

[version %s]
Written and tested in python3.6. Adapted from Jirka Novacek

Pavel Afanasyev
https://github.com/afanasyevp/afis
=================================================================================================

''' % ver 
    

    parser = argparse.ArgumentParser(description="")
    add=parser.add_argument
    add('--i',  help="Directory with all the xml and movies files")
    add('--o', default="", help="Output star file. If empty no file generated generated.")
    add('--f', type=str,   help="File format (mrc, mrcs, tiff, tif)")
    add('--o_shifts', default="", help="Output file with extracted beam-shifts and cluster numbers. If empty no file generated generated.")
    add('--clusters', type=str, default="9", help="Number of clusters the beam-shifts should be divided in. (default: 1)")
    add('--elbow', type=str, default="0", help="Number of max clusters used in Elbow method optimal cluster number determination. (default: 0)")
    add('--max_iter', type=str, default="300", help="Expert option: Maximum number of iterations of the k-means algorithm for a single run. (default: 300)")
    add('--n_init', type=str, default="10", help="Expert option: Number of time the k-means algorithm will be run with different centroid seeds. (default: 10)")
    add('--pix', default='1', help="Pixel size. Default value: 1 A/pix")
    add('--kev', type=str, default='300', help="keV. Default value: 300")
    add('--cs', type=str, default='2.7', help="Cs. Default value: 2.7")
    add('--amp_con', type=str, default='0.1', help="Amplitude contrast. Default value: 0.1")
    args = parser.parse_args()
    print(output_text)
    parser.print_help()
    print("Example: optics_split.py --i ./movies --o movies.star --f tiff --clusters 9 --pix 1.09")
    print(" ")
    #print("args: ", args)
    try:
        clusters = int(args.clusters)
        elbow = int(args.elbow)
        max_iter = int(args.max_iter)
        n_init = int(args.n_init)
    except ValueError:
        print("--clusters, --elbow, --max_iter and --n_init require integer values for comparison.")
        sys.exit(2)
    if len(sys.argv) == 1:
        #parser.print_help()
        sys.exit(2)
    if not args.i:
        print("No input file given.")
        #parser.print_help()
        sys.exit(2)
    elif str(args.i)[-1] != "/":
        directory=args.i+"/"
    else:
        directory=str(args.i) 
    if not args.o:
        print("No output file given. No star file will be saved.")
    if not os.path.exists(args.i):
        print("Input directory '%s' not found." % args.i)
        sys.exit(2)
    if not args.f:
        print("Movie format is not found.")
        sys.exit(2)
    pxl_size=args.pix
    kev=args.kev
    cs=args.cs 
    amp_con=args.amp_con
    #print(directory)
    movietype=args.f
    xml_files, movie_files=get_files(directory, movietype)
    #print(xml_files)
    #print(movie_files)
    beamShiftArray=get_beamShiftArray(xml_files, args.i)
    #print (beam_shift_array[0])
    

    if elbow > 0:
        print("Running elbow....")
        elbowMethod(elbow, beamShiftArray, max_iter, n_init)
        print("Elbow done!")
    else:
        print("Running Kmeans....")
        pred_y = kmeansClustering(clusters, beamShiftArray, max_iter, n_init)
        print("Kmeans done!")
    if (not args.o == "") and elbow == 0:
        saveStarFile(args.o, movie_files, pred_y, pxl_size, kev, cs, amp_con, clusters)
    if (not args.o_shifts == "") and elbow == 0:
        saveClusteredShifts(args.o_shifts, beamShiftArray, pred_y)
    #print (pred_y)
    #print(len(pred_y))
    print("\nThe program finished successfully. Please critically check the results in the %s file." % args.o)
if __name__ == '__main__':
    main()

