import logging
logging.basicConfig(filename='./camfinger.log', level=logging.ERROR,
format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

import PIL.ExifTags
from PIL import Image

import exiftool

import mysql.connector
import pandas as pd
import numpy as np

from pathlib import Path

import sys

import qtables as q
import pickle

def get_db_pw(fname='/localhome/patrick/.ssh/.magicfern.pw'):
    with open(fname) as f:
        content = f.readlines()
    if len(content) > 1:
        print('most likely erronous password-file: {}'.format(fname))

    return content[0].split('\n')[0]


def get_exif(filename, path = '/disks/data3/camfinger-images/'):
   
    fullfile = path + filename

    if not Path(fullfile).is_file():
        exif = {'hasExifFields': -1, 'FileName': filename}
        nonconform_exif = {'hasNonConformExifFields':-1, 'FileName': filename}
        return exif, nonconform_exif 

    im = Image.open(fullfile)
    exif = {}
    nonconform_exif = {}

    if im._getexif() == None:
        hasExifFields = 0
        hasNonConformExifFields = 0
    else:
        exif = {
            PIL.ExifTags.TAGS[k]: v
                for k, v in im._getexif().items()
                if k in PIL.ExifTags.TAGS
        }
        nonconform_exif = {
            k: v
                for k, v in im._getexif().items()
                if k not in PIL.ExifTags.TAGS
        }
        hasExifFields = len(exif)
        hasNonConformExifFields = len(nonconform_exif)
    
    exif['hasExifFields'] = hasExifFields
    exif['FileName'] = filename
    nonconform_exif['hasNonConformExifFields'] = hasNonConformExifFields
    nonconform_exif['FileName'] = filename
    im.close()
    return exif, nonconform_exif


def get_qtable(filename, qtable_list, qtable_histogram, grey_table=0, path = '/disks/data3/camfinger-images/'):
    """
    grey_table=0 -> Y-Table
    grey_table=1 -> CbCr-Table
    """
    fullfile = path + filename
    if not Path(fullfile).is_file():
        return np.nan, qtable_list, qtable_histogram 
    
    im = Image.open(fullfile)
    qtable = im.quantization[grey_table]
    qtable_index = q.find_qtable_index(qtable, qtable_list)
    qtable_list, qtable_histogram = q.append_qtable(qtable_index, qtable, qtable_list, qtable_histogram)
    return qtable_index, qtable_list, qtable_histogram

def get_metadata_from_exiftool(filename_list, path =
        '/disks/data3/camfinger-images/'):
    """
    Get EXIF (and more) by utilizing Phil Harvey's ExifTool
    """
    print('Run ExifTool ', end='', flush=True)
    # remove invalid filename entries
    filename_list[:] = [path + filename for filename in filename_list if Path(path +
        filename).is_file()]
    print('for {} files. '.format(len(filename_list)),end = '\n', flush=True)
    # get metadata
    metadata = []
    with exiftool.ExifTool() as et:
        for i,f in enumerate(filename_list):
            try:
                if i % 100 == 0:
                    print('{}/{}'.format(i,len(filename_list)),end='\r')
                metadata.append(et.get_metadata(f))
            except Exception as e:
                print('Error in: \n{}\n{}\n'.format(f,f))
                logging.error('#{} File: {} Exception: {}'.format(i, f, e))
        
    print('Done', end='\n', flush=True)
    return metadata

path = '/disks/data3/images/'

# Read mysql db from server and save in pd DataFrame
p = get_db_pw()
mConn = mysql.connector.connect(user='mullanptr', password=get_db_pw(), host='b.moneygun.cs.fau.de', database='magicfern', charset='utf8mb4')
df_mysql = pd.read_sql("SELECT * FROM users INNER JOIN images ON users.username = images.user;", con=mConn)
mConn.close()

## Rename keys of mysql DB in df_mysql by adding a suffix
#for k, v in enumerate(df_mysql.keys()):
#    df_mysql.rename(columns={v: v + '_cf'}, inplace=True)

d = [] # dataframe for exif
dn = [] # dataframe for nonconform_exif

dq = [] # dataframe for quantization tables (Y)
qtable_list = []
qtable_histogram = []

dc = [] # dataframe for quantization tables (CbCr)
ctable_list = []
ctable_histogram = []

et = [] # dataframe for exif extracted with ExifTool

for i, f in enumerate(df_mysql.filename):

    e, n = get_exif(f, path=path)
    d.append(e)
    dn.append(n)
    
    qtable_index, qtable_list, qtable_histogram = get_qtable(f, qtable_list,
            qtable_histogram, path=path)
    if not np.isnan(qtable_index):
        dq.append({'q':qtable_index,'filename':f})
    ctable_index, ctable_list, ctable_histogram = get_qtable(f, ctable_list,
            ctable_histogram, grey_table=1, path=path)
    if not np.isnan(ctable_index):
        dc.append({'c':ctable_index,'filename':f})

    if i % 100 == 0:
        print('{}/{}'.format(i,len(df_mysql)),end='\r')

metadata = get_metadata_from_exiftool(df_mysql.filename.tolist(), path=path)

df_exif = pd.DataFrame(d)
df_non = pd.DataFrame(dn)
df_q = pd.DataFrame(dq)
df_c = pd.DataFrame(dc)
df_metadata = pd.DataFrame(metadata)

df_exif.to_pickle('df_exif.pickle')    
df_non.to_pickle('df_nonconform.pickle')
df_mysql.to_pickle('df_mysql.pickle')
df_q.to_pickle('df_q.pickle')
with open('qtable_list.pickle','wb') as f:
    pickle.dump(qtable_list, f)
df_c.to_pickle('df_c.pickle')
with open('ctable_list.pickle','wb') as f:
    pickle.dump(ctable_list, f)
df_metadata.to_pickle('df_metadata.pickle')
