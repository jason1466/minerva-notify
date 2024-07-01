"""
Main module for minerva scanner.
Performs check loop and reads command line arguments.
"""

import time, chime
import argparse
import sys
import logging


import course_check
from notify import send_mail

root = logging.getLogger()
root.setLevel(logging.INFO)

class Course:
    def __init__(self, dept, term, crn, num):
        self.department = dept
        self.term = term
        self.crn = crn
        self.course_number = num
        self.status = None
        self.spots = None
        self.wl_spots = None

    def __str__(self):
        return f"{self.department.upper()} {self.course_number.strip()} in {self.term.strip()}, status is {self.status} and has {self.spots.strip()} spots open {self.wl_spots.strip()} waitlist spots open"

def cline():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--courselist', type=str, help='Path to course file to\
        watch', default="watchlist.txt")
    parser.add_argument('--logins', type=str, help='Path to login info.',\
        default="logins.txt")
    parser.add_argument('--interval', type=int, help='Number of minutes\
        wait between checks.', default=0.5)
    parser.add_argument('--login_interval', type=int, help='Number of minutes\
        wait between logout/login. Under 30 minutes may result in account being\
            locked.', default=480)
    parser.add_argument('--summary', type=int, help='Number of hours\
        between summary email sent with status of all watched courses.',\
            default=2)
    args = parser.parse_args()

    return args
def load_login(fpath="logins.txt"):
    """
    Parse file with mcgill and gmail login info.
    Expected format:
    <mcgill email> <mcgill password>
    <gmail email>  <gmail password>

    Returns: dict
    """
    
    with open(fpath, "r") as f:
        login_dict = {}
        for i, l in enumerate(f):
            info = l.split()
            try:
                email = info[0].strip()
                password = info[1].strip()
                username = email.split("@")[0]
                service = email.split("@")[1]
            except IndexError:
                logging.critical("Incorrect email format.")
                sys.exit(1)

            if service == "mcgill":
                login_dict['mcgill_username'] = username
                login_dict['mcgill_password'] = password

            elif service == "windowsoft.com":
                login_dict['gmail_email'] = email
                login_dict['gmail_password'] = password 
        
            else:
                logging.critical("Unrecognized email service.")
                sys.exit(1)
    return login_dict 

def load_courses(fpath="watchlist.txt"):
    courses = []
    with open(fpath, "r") as cfile:
        for line in cfile:
            try:
                dept, cnum, crn, term = line.split(",")
                course = Course(dept.upper(), term.strip(), crn, cnum)
                courses.append(course)
            except:
                print("Invalid Course Entry")
    return courses

def main_loop(logins, courses, interval=4, login_interval=60, mail_time=6):
    """
    Monitor minerva for each course and send email if useful changes occur.
    """

    chime.theme('big-sur')

    last_summary= time.time()

    logging.info("Starting course watch...")
    logging.info(f"Querying courses every {interval} minutes.")
    logging.info(f"Logging in every {login_interval} minutes.")
    logging.info(f"Summary emails sent every {mail_time} hours.")

    count = 0
    #login
    logging.info("Logging in...")
    try:
        course_check.login(logins['mcgill_username'], logins['mcgill_password'])

    except:
        logging.critical("Login error.")
        sys.exit(1)

    while True:
        time_now = time.strftime("%a, %d %b %Y %H:%M:%S +0000",\
        time.localtime(time.time()))

        logging.info(f">> Latest Status {time_now}")

        message = ["Subject: Scheduled Minerva Summary"]
        for course in courses:
            info = course_check.check_availability(course.course_number, course.crn,\
                term=course.term, dept=course.department)
            
            try:
                status = info['status']
            except:
                status = "Active"

            try:
                spots = info['spots']
            except:
                spots = 2

            try:
                wait_spots = info['wait_spots']
            except:
                wait_spots = 0

            try:
                register_attempted_crn = info['register_attempted_crn']
            except:
                register_attempted_crn = None

            course.status = status
            course.spots = spots
            course.wl_spots = wait_spots

            if (int(wait_spots) > 0):
                for i in range(10):
                    print("Go >> ", course.course_number)
                    time.sleep(1)
                    chime.success()
                send_mail(logins['gmail_email'], logins['gmail_password'],\
                    logins['gmail_email'],\
                        f"Subject: Minerva Course Change Alert! @ {time_now}\n\n" + course.__str__())


            first_time = course.status is None and course.spots is None
            free_spots = int(spots) > 0 and spots != course.spots

            #if status for course changes, send email
            if (status != course.status or free_spots) and not first_time:
                
                for i in range(10):
                    time.sleep(1)
                    chime.success()

                send_mail(logins['gmail_email'], logins['gmail_password'],\
                    logins['gmail_email'],\
                        f"Subject: Minerva Course Change Alert! @ {time_now}\n\n" + course.__str__())

            logging.info(course.__str__())
            message.append(course.__str__())

        # send summary email
        hours_since_summary = int((time.time() - last_summary) / 3600)
        logging.info(f"Hours since last summary: {hours_since_summary}")
        if hours_since_summary == mail_time:
            logging.info("Sending summary email.")
            last_summary = time.time()
            send_mail(logins['gmail_email'], logins['gmail_password'],\
                logins['gmail_email'], "\n".join(message))
            
        count = count + 1

        if (register_attempted_crn):
            courses = [course for course in courses if course.crn != register_attempted_crn]

        if count == (login_interval / interval):
            logging.info("Logging out...")
            course_check.logout()
            time.sleep(5)
            #login
            logging.info("Logging back in...")
            try:
                course_check.login(logins['mcgill_username'], logins['mcgill_password'])

            except:
                logging.critical("Login error.")
                sys.exit(1)

        #sleep for interval minutes 
        logging.info(f"Sleeping for {interval} minutes...")
        time.sleep(interval * 60)


if __name__ == "__main__":
    args = cline()
    logins = load_login(fpath=args.logins)
    courses = load_courses(fpath=args.courselist)
    main_loop(logins, courses, interval=args.interval, login_interval=args.login_interval, mail_time=args.summary)
    pass
