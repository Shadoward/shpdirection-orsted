#!/usr/bin/env python -u
# -*- coding: utf-8 -*-
###############################################################
# Author:       patrice.ponchant@furgo.com  (Fugro Brasil)    #
# Created:      17/12/2020                                    #
# Python :      3.x                                           #
###############################################################

# The future package will provide support for running your code on Python 2.6, 2.7, and 3.3+ mostly unchanged.
# http://python-future.org/quickstart.html
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

##### Basic packages #####
import sys
import datetime
import re
from collections import Iterable

##### Shapefiles packages #####
from shapely.geometry import Point, mapping, shape
import fiona
import geopandas as gpd
import math

##### GUI packages #####
from gooey import Gooey, GooeyParser
from colored import stylize, attr, fg

# 417574686f723a205061747269636520506f6e6368616e74
##########################################################
#                       Main code                        #
##########################################################
# https://pythonpedia.com/en/knowledge-base/30635145/create-multiple-dataframes-in-loop

# this needs to be *before* the @Gooey decorator!
# (this code allows to only use Gooey when no arguments are passed to the script)
if len(sys.argv) >= 2:
    if not '--ignore-gooey' in sys.argv:
        sys.argv.append('--ignore-gooey')
        
# Preparing your script for packaging https://chriskiehl.com/article/packaging-gooey-with-pyinstaller
# Prevent stdout buffering # https://github.com/chriskiehl/Gooey/issues/289

# GUI Configuration
@Gooey(
    program_name='Find direction information from Preplot .shp file and add the Post-Plot .shp file',
    richtext_controls=True,
    #richtext_controls=True,
    terminal_font_family = 'Courier New', # for tabulate table nice formatation
    #dump_build_config=True,
    #load_build_config="gooey_config.json",
    default_size=(600, 550),
    timing_options={        
        'show_time_remaining':True,
        'hide_time_remaining_on_complete':True
        },
    header_bg_color = '#95ACC8',
    #body_bg_color = '#95ACC8',
    menu=[{
        'name': 'File',
        'items': [{
                'type': 'AboutDialog',
                'menuTitle': 'About',
                'name': 'shpdirectionorsted',
                'description': 'Find direction information from Preplot .shp file and add the Post-Plot .shp file',
                'version': '0.1.0',
                'copyright': '2020',
                'website': 'https://github.com/Shadoward/shpdirection-orsted',
                'developer': 'patrice.ponchant@fugro.com',
                'license': 'MIT'
                }]
        }]
    )

def main():
    desc = "Find direction information from Preplot .shp file and add the Post-Plot .shp file"    
    parser = GooeyParser(description=desc)
    
    main = parser.add_argument_group('Main', gooey_options={'columns': 1})
    
    main.add_argument(
        '-b',
        '--preplot', 
        dest='preplot',       
        metavar='Preplot .shp File', 
        help='Preplot .shp file to be use for line direction',
        widget='FileChooser',
        gooey_options={'wildcard': "Shapefiles (.shp)|*.shp"})
    
    main.add_argument(
        '-a',
        '--postplot', 
        dest='postplot',       
        metavar='Post-Plot .shp File', 
        help='Post-Plot .shp file to be use to add line direction from Preplot',
        widget='FileChooser',
        gooey_options={'wildcard': "Shapefiles (.shp)|*.shp"})
    
    main.add_argument(
        '-o', '--output',
        dest='outputFolder',
        metavar='Output Folder',  
        help='Output folder to save the .shp files.',      
        widget='DirChooser')
    
    
    # Use to create help readme.md. TO BE COMMENT WHEN DONE
    # if len(sys.argv)==1:
    #    parser.print_help()
    #    sys.exit(1)   
        
    args = parser.parse_args()
    process(args)

def process(args):
    """
    Uses this if called as __main__.
    """
    
    preplot = args.preplot
    postplot = args.postplot
    outputFolder =args.outputFolder 
    
    print('', flush=True)
    print(f'Merging the shapefiles files.\n{preplot}\n{postplot}\nPlease wait.......', flush=True)
    
    # Read Preplot and create the azimuth and az_reverse columns
    with fiona.collection(preplot, 'r') as inputPre:
        # copy of the inputPre schema'
        schemaPre = inputPre.schema.copy()
        crsPre = inputPre.crs
        # creation of a new field for storing azimuth
        schemaPre['properties']['azimuth'] = 'int'
        schemaPre['properties']['az_reverse'] = 'int'
        # copy of the original shapefile with the field azimuth to a new shapefile
        with fiona.collection(outputFolder + '\\preplot_with_azimuths.shp', 'w', 
                              crs=crsPre, driver='ESRI Shapefile', schema=schemaPre) as outputPre:
            for line in inputPre:
                line_start = Point(line['geometry']['coordinates'][0])
                line_end = Point(line['geometry']['coordinates'][-1])
                line['properties']['azimuth'] = azimuth(line_start, line_end)
                line['properties']['az_reverse'] = azimuth_reverse(line_start, line_end)
                # https://gis.stackexchange.com/questions/104312/multilinestring-to-separate-individual-lines-using-python-with-gdal-ogr-fiona         
                if line['geometry']['type'] == 'MultiLineString':
                    for elem in shape(line['geometry']): 
                        outputPre.write({'geometry':mapping(elem),'properties':line['properties']})
                elif line['geometry']['type'] == 'LineString':
                    outputPre.write({'geometry':mapping(shape(line['geometry'])),'properties':line['properties']})      

    dfPreplot = gpd.read_file(outputFolder + '\\preplot_with_azimuths.shp')    
    if not {'LinePrefix', 'LineNumber'}.issubset(dfPreplot.columns):
        sys.exit(stylize('No LinePrefix or LineNumber columns found in the Post-plot file, quitting', fg('red')))
    dfPreplot = dfPreplot[['LinePrefix', 'LineNumber', 'azimuth', 'az_reverse']]
    dfPreplot['LineName'] = dfPreplot['LinePrefix'].astype(str) + dfPreplot['LineNumber'].astype(str)
    
    with fiona.collection(postplot, 'r') as inputPost:
        # copy of the inputPost schema'
        schemaPost = inputPost.schema.copy()
        crsPost = inputPost.crs
        # creation of a new field for storing azimuth
        schemaPost['properties']['az_line'] = 'int'
        schemaPost['properties']['az_preplot'] = 'int'
        schemaPost['properties']['az_list'] = 'str'
        schemaPost['properties']['LN_preplot'] = 'str'
        schemaPost['properties']['To_Verify'] = 'str'
        
        # copy of the original shapefile with the field azimuth to a new shapefile
        with fiona.collection(outputFolder + '\\postplot_azimuth_from_preplot.shp', 'w', 
                              crs=crsPost, driver='ESRI Shapefile', schema=schemaPost) as outputPost:
            for line in inputPost:
                line_start = Point(line['geometry']['coordinates'][0])
                line_end = Point(line['geometry']['coordinates'][-1])
                az_line = azimuth(line_start, line_end) # live like that use somewhere else

                line['properties']['az_line'] = az_line
                az_post = azimuth(line_start, line_end)                
                if not line['properties']['Line']:
                     sys.exit(stylize('No File_Name column found in the Post-plot file, quitting', fg('red')))
                Linename = re.sub('\D', '', line['properties']['Line'])
                
                dffilter = dfPreplot.loc[dfPreplot['LineNumber'] == int(Linename)]
               
                azls_tmp = dffilter[['azimuth', 'az_reverse']].values.tolist() if not dffilter.empty else None
                azls_preplot = list(flatten(azls_tmp)) if not dffilter.empty else []

                az_final = int(min(azls_preplot, key=lambda x:abs(x-az_post))) if not dffilter.empty else 999
                line['properties']['LN_preplot'] = str(dffilter['LineName'].values.tolist()) if not dffilter.empty else ""
                line['properties']['az_preplot'] = az_final  
                line['properties']['az_list'] = str(azls_preplot)
                # From QC
                if abs(az_final - az_line) > 5:
                    line['properties']['To_Verify'] = "To_Be_Verified"
                elif not azls_preplot:
                    line['properties']['To_Verify'] = "To_Be_Verified"
                elif len(azls_preplot) > 2:
                    line['properties']['To_Verify'] = "To_Be_Verified"
                elif line['properties']['Direction']:
                    if abs(int(float(line['properties']['Direction'])) - az_final) > 5:
                        line['properties']['To_Verify'] = "To_Be_Verified"
                    else:
                        line['properties']['To_Verify'] = ""
                else:
                    line['properties']['To_Verify'] = ""
                    
                #print(f'az_list_preplot: {azls_preplot}', flush=True)
                #print('#########################', flush=True)                
                if line['geometry']['type'] == 'MultiLineString':
                    for elem in shape(line['geometry']): 
                        outputPost.write({'geometry':mapping(elem),'properties':line['properties']})
                elif line['geometry']['type'] == 'LineString':
                    outputPost.write({'geometry':mapping(shape(line['geometry'])),'properties':line['properties']})     


def azimuth(point1, point2):
    '''azimuth between 2 shapely points'''
    degBearing = round(math.degrees(math.atan2((point2.x - point1.x),(point2.y - point1.y))),0)
    if (degBearing < 0):
        degBearing += 360.0
    return degBearing

def azimuth_reverse(point1, point2):
    '''azimuth between 2 shapely points'''
    degBearing = round(math.degrees(math.atan2((point2.x - point1.x),(point2.y - point1.y))) + 180,0)
    if (degBearing < 0):
        degBearing += 360.0
    return degBearing

def pair(list):
    '''Iterate over pairs in a list '''
    for i in range(1, len(list)):
        yield list[i-1], list[i]

# function used for removing nested  
# https://stackoverflow.com/questions/17485747/how-to-convert-a-nested-list-into-a-one-dimensional-list-in-python
def flatten(lis):
     for item in lis:
         if isinstance(item, Iterable) and not isinstance(item, str):
             for x in flatten(item):
                 yield x
         else:        
             yield item

##########################################################
#                        __main__                        #
########################################################## 
if __name__ == "__main__":
    now = datetime.datetime.now() # time the process
    main()
    print('', flush=True)
    print("Process Duration: ", (datetime.datetime.now() - now), flush=True) # print the processing time. It is handy to keep an eye on processing performance.