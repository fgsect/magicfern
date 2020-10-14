import os

import mysql.connector
    
MAGICFERN_BINARY_PATH = "/path/to/magicfern/MagicFern"

IMAGES_DIR_PATH = "/media/storage/camfinger/images"
IMAGES_CROPPED_DIR_PATH = "/media/storage/camfinger/images_cropped"


_mConns = {}

def get_mysql_connection():
    thread_id = os.getpid()  # threading.get_ident()
    # XXX: THE FOLLOWING LINE DISABLES THE CONNECTION PER PROCESS/THREAD FEATURE
    #thread_id = 1
    if not thread_id in _mConns.keys():
        try:
            _mConns[thread_id] = mysql.connector.connect(user='magicfern_user', password='THE_PASSWORD',
                                   host='THEHOST', database="magicfern",
                                  charset='utf8mb4', buffered=True)
        except:
            raise Exception("Could not get a MySQL connection!")

    return _mConns[thread_id]

try:
    from local_config import *

except Exception as ex:
    print("local_config not loaded - using defaults", ex)
    # No local config, no worries.
