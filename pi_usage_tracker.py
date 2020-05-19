import logging
import sqlite3
import os
import smtplib
from email.message import EmailMessage
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

def send_email():
    # Retrieving config for Gmail
    EMAIL_ADDRESS = os.environ.get('GMAIL_USER')
    EMAIL_PASSWORD = os.environ.get('GMAIL_PASS')

    msg = EmailMessage()
    msg['Subject'] = 'Threshold Exceeded'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = 'timurmustafa1989+raspi@gmail.com'

    msg.set_content(f"Current temp: {current.cpu}. Threshold exceeded: {current.cpu_threshold}\nCurrent load average: {current.la}. Threshold exceeded: {current.la_threshold}\nCurrent disk usage: {current.disk}%. Threshold exceeded: {current.disk_threshold}")

    if real_run:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
    else:
        # Run this command in terminal before running the app to run a debug server on your local to see these messages.
        # python3 -m smtpd -c DebuggingServer -n localhost:1025
        with smtplib.SMTP('localhost', 1025) as smtp:
            smtp.send_message(msg)

class PiStats:
    def __init__(self, cpu, la, disk):
        logger.debug(f"Initialising PiStats Object")
        if real_run:
            self.cpu = cpu.temperature
            self.la = la.load_average
            # Round the disk usage to 2 decimal places
            self.disk = disk.usage
            try:
                self.cpu_threshold = cpu.is_active
                self.la_threshold = la.is_active
                self.disk_threshold = disk.is_active
            except Exception as e:
                logger.exception(f"Exception raised: {e}")
        else:
            self.cpu = cpu
            self.la = la
            self.disk = disk
            self.cpu_threshold = False
            self.la_threshold = False
            self.disk_threshold = True
        logger.info(f"Successfully initialised PiStats Object")

if real_run:
    cpu = CPUTemperature(min_temp=50, max_temp=90, threshold=70)
    la = LoadAverage(min_load_average=0, max_load_average=2, threshold=1)
    disk = DiskUsage(threshold=80)
else:
    cpu = 12
    la = 20
    disk = 89

current = PiStats(cpu, la, disk)
insert_to_db(datetime.now(), current.cpu, current.la, current.disk)

# Add in notification system for thresholds
if current.cpu_threshold or current.la_threshold or current.disk_threshold:
    logger.warning(f"Threshold exceeded: CPU {current.cpu_threshold}, Load Avg {current.la_threshold}, Disk % {current.disk_threshold}")
    send_email()
else:
    logger.info(f"No thresholds exceeded")