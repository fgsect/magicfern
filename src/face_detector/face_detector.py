import face_recognition
import pandas as pd
import os

def get_img_file(fname, path='/media/storage/camfinger/images/'):
    fl = os.path.join(path,fname)
    return fl

def isFile(fname, path='/media/storage/camfinger/images/'):
    fl = os.path.join(path,fname)
    return os.path.isfile(fl)


table_df = pd.read_csv('~/table.tsv',sep='\t')
print(f'Read in table of shape {table_df.shape}')

table_df['isFile'] = table_df.filename.apply(lambda fname: isFile(fname=fname))
table_df = table_df.loc[table_df.isFile]

table_df['SourceFile'] = table_df.filename.apply(lambda fname: get_img_file(fname=fname))

print(f'table_df has valid imgs: {table_df.__len__()}')

face_locs = {
    SF: face_recognition.face_landmarks(face_recognition.load_image_file(SF))
    for SF in table_df.SourceFile.tolist()
}

face_ser = pd.Series(face_locs)
face_ser.to_csv('face_ser.csv', delim=':')

