import logging
import sqlite3
from datetime import datetime
from gpiozero import CPUTemperature, LoadAverage, DiskUsage

# Config for REAL run or TEST run
real_run = True

# Setting up the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

log_formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')

log_file_handler = logging.FileHandler('pi_usage_tracker.log')
log_file_handler.setFormatter(log_formatter)

logger.addHandler(log_file_handler)

def insert_to_db(date, cpu_temp, load_avg, disk_usage):
    db = sqlite3.connect('pi_usage_tracker.db')
    c = db.cursor()
    c.execute ('''CREATE TABLE IF NOT EXISTS stats (
      id integer primary key, 
      date text, 
      cpu_temp integer, 
      load_avg integer, 
      disk_usage integer
    );''')
    try:
        sql_insert = f"INSERT INTO stats (date, cpu_temp, load_avg, disk_usage) VALUES ('{date}', {cpu_temp}, {load_avg}, {disk_usage});"
        logger.debug(f"Attempting to INSERT to DB: {sql_insert}")
        c.execute(sql_insert)
        db.commit()
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
    except Exception as e:
        logger.exception(f"Exception raised: {e}")
    finally:
        if db:
            logger.debug(f"INSERT to DB SUCCESSFUL")
            db.close()
    return True

class PiStats:
    def __init__(self, cpu, la, disk):
        logger.debug(f"Initialising PiStats Object")
        if real_run:
            self.cpu = cpu.temperature
            self.la = la.load_average
            self.disk = disk.usage
        else:
            self.cpu = cpu
            self.la = la
            self.disk = disk
            
        try:
            self.cpu_threshold = cpu.is_active
            self.la_threshold = la.is_active
            self.disk_threshold = disk.is_active
        except Exception as e:
            logger.exception(f"Exception raised: {e}")
        logger.info(f"Successfully initialised PiStats Object")

if real_run:
    cpu = CPUTemperature(min_temp=50, max_temp=90, threshold=70)
    la = LoadAverage(min_load_average=0, max_load_average=2, threshold=1)
    disk = DiskUsage(threshold=80)
else:
    cpu = 12
    la = 20
    disk = 50

current = PiStats(cpu, la, disk)
insert_to_db(datetime.now(), current.cpu, current.la, current.disk)

# Add in notification system for thresholds
if current.cpu_threshold or current.la_threshold or current.disk_threshold:
    logger.warn(f"Threshold exceeded: CPU {current.cpu_threshold}, Load Avg {current.la_threshold}, Disk % {current.disk_threshold}")
    # Send email notif
logger.info(f"No thresholds exceeded")

print(f"Current temp: {current.cpu}")
print(f"Current load average: {current.la}")
print(f"Current disk usage: {current.disk}%")