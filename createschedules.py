# Jerry Day
# 4/26/2021

import pandas as pd
import os
import re
import moviemodel
import datetime

def check_and_make_schedules():
    data_in_dirs = [f for f in os.scandir('DataIn') if f.is_dir() & (f.name != '.ipynb_checkpoints')]

    schedules_have = [f.name for f in os.scandir('Schedules') if f.is_file() & bool(re.search('.+\.csv$',f.name))]

    for did in data_in_dirs:
        if did.name + "_Schedule.csv" not in schedules_have:
            moviemodel.generateSchedule(pd.read_csv(did.path + "/Theatre_Bookings.csv"), 
                     pd.read_csv( did.path + "/Theatre_Details.csv"),  
                     TUsize = 15, 
                     startTime = datetime.datetime.strptime("08/29/21 11:30:00", '%m/%d/%y %H:%M:%S'),
                     endTime = datetime.datetime.strptime("08/29/21 20:45:00", '%m/%d/%y %H:%M:%S')
                    ).to_csv("Schedules/"+ did.name + "_Schedule.csv",index = False)
    return None

if __name__ == "__main__":
    check_and_make_schedules()