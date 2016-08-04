# -*- coding:  utf-8 -*-
import subprocess
import time
import smtplib
import datetime
import ConfigParser
import os
import sys
import logging

cfg_pstools_path = "c:\pstools"

__version__ = '0.2'

def initLogging(logFilename):
    """Init for logging
    """
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y/%m/%d %H:%M:%S',
        filename=logFilename,
        filemode='a')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

def check_service(service_name):
    cmd = "%s\psservice.exe" % (cfg_pstools_path)
    pst = subprocess.Popen(
            [cmd, "query", service_name],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE
        )

    out, error = pst.communicate()

    if out.find('RUNNING') > 0:
        return True
    else:
        return False

def start_service(service_name):
    cmd = "%s\psservice.exe" % (cfg_pstools_path)
    pst = subprocess.Popen(
            [cmd, "start", service_name],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE
        )

    out, error = pst.communicate()

    if pst.returncode is not 0:
        return False
    return True

def mail(serverURL=None, strFrom='', strTo='', subject='', text=''):
    smtp = smtplib.SMTP()
    smtp.connect(serverURL)
    for x in strTo:
        headers = 'From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n' % (
            strFrom, x, subject)
        message = headers + text
        smtp.sendmail(strFrom, x, message)
    smtp.quit()

def main():
    start_time = datetime.datetime.now().strftime('%Y_%m_%d %H:%M:%S')
    path = os.path.realpath(os.path.dirname(sys.argv[0]))
    cnf_file = path + '\ps_check_service.cnf'
    config = ConfigParser.ConfigParser()
    config.read(cnf_file)
    service_list = [e.strip() for e in config.get('main', 'service_list').split(',')]
    error_code = 0

    logfile = path + '\ps_check_service.log'
    initLogging(logfile)
    logging.info('check service %s version: %s' % (start_time, __version__))
    
    if os.path.exists("script_status.txt"):
        logging.info('system is running or last time error, please check %s version:%s' % (start_time, __version__))
        service_list = []
        error_code = 1
    else:
        f = file("script_status.txt", "w")
        f.write(start_time)
        f.close()

    check_time = {}
    wait_time = 300
    mailserver = config.get('main', 'mailserver')
    sent = config.get('main', 'sent')

    contacts = [e.strip() for e in config.get('main', 'contacts').split(',')]

    for i in service_list:
        out = check_service(i)
        logging.info("check %s" % (i))

        if out == False:
            start_service(i)
            logging.info("service: %s" % (i))
            logging.info("service restart")
            logging.info("wait: %s" % (90))
            time.sleep(90)
            out = check_service(i)
            if out == False:
                check_time[i] = 1
                while check_time[i] < 3:
                    logging.info("wait_time: %s" % (wait_time))
                    time.sleep(wait_time)
                    start_service(i)
                    logging.info("service: %s service restart" % (i))
                    logging.info("wait: %s" % (90))
                    time.sleep(90)
                    out = check_service(i)
                    if out == False:
                        a = check_time[i]
                        a = a + 1
                        check_time[i] = a
                        error_code = 1
                    else:
                        error_code = 0
                if out == False and error == 1:
                    now = datetime.datetime.now().strftime('%Y_%m_%d %H:%M:%S')
                    subject = 'sapb1 %s service down please check %s' % (i, now)
                    msg = 'sapb1 %s service down please check %s' % (i, now)
                    logging.info("restart %s service fail time: %s" % (i, now))
                    mail(mailserver, sent, contacts, subject, msg)

    if error_code == 0:
        logging.info("check all done")
        os.remove("script_status.txt")

if __name__ == '__main__':
    main()