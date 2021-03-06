import os, webbrowser
from datetime import datetime
from pathlib import Path
from canvasapi import Canvas, exceptions
from ccssrg_classes import *
from ccssrg_functions import *

CANVAS_URL = "tulsaps.instructure.com"

def main(**kwargs):

    try:
        kwargs['version']
    except:
        version = "0.6d"
    else:
        version = kwargs['version']

    userprefs = UserPrefs()
    userprefs.file = "prefs.json"

    try:
        kwargs['flask']
    except:
        flask_run = False
    else:
        flask_run = True

    if flask_run:
        token = kwargs['access_token']
        canvas_base_url = "https://" + kwargs['canvas_base_url']
        userprefs.canvas_url = canvas_base_url
        selected_courses = kwargs['selected_courses']

        try:
            canvas = Canvas(canvas_base_url, token)
            user = canvas.get_current_user()
            userprefs.name = user.name
        except:
            script_path = os.path.dirname(__file__)
            filename = os.path.join(script_path, 'error.html')
            return filename
    
    if not flask_run:
        prefs = access_prefs(userprefs)

        token = userprefs.token
        canvas_base_url = "https://" + CANVAS_URL
        userprefs.canvas_url = canvas_base_url
        canvas = Canvas(canvas_base_url, token)
        
        while True:
            try:
                user = canvas.get_current_user()
            except exceptions.InvalidAccessToken as e:
                print(e.message[0]['message'])
                print("Authorization Failure. Is your token correct?")
                prefs = access_prefs(userprefs)
            else:
                print(f"Successfully connected for {user.name} ({user.id})")
                userprefs.name = user.name
                break
    
    print(f"Setting up reporting environment...\n")
    report_time = datetime.now()
    report_time_file = report_time.strftime("%Y%m%d-%H%M%S")
    
    script_path = os.path.dirname(__file__)
    reports_path = os.path.join(script_path, 'reports')
    Path(reports_path).mkdir(parents=True, exist_ok=True)
    filename = f"{reports_path}/{user.name}_{report_time_file}.html"

    obj_report = open(filename, 'a+', encoding='utf-8') 
    initialize_report(obj_report, user.name, report_time) 

    profile = user.get_profile()
    time_zone = profile['time_zone']

    inbox_messages = canvas.get_conversations(scope="unread")

    if len(list(inbox_messages)) > 0:
        print(f"{user.name} has unread messages in Inbox!")
    write_inbox(obj_report, user, time_zone, inbox_messages, canvas_base_url)
    
    print(f"Accessing Canvas for Courses for: {user.name} (may take a moment)...\n")
    courses = user.get_courses(
        state=["available"], enrollment_state="active",
        include=["tabs", "total_scores"]
        )
    
    if courses:
        if flask_run == False:
            selected_courses = select_courses(user, courses, userprefs)
            ''' Write preference to file after course selection '''
            write_prefs_file(userprefs)
        else:
            if len(selected_courses) == 0:
                for course in courses:
                    selected_courses.append(course.id)

        run_time_start = now_utc()

        for course in courses:
            if course.id in selected_courses:
                print(f"Accessing Canvas for assigments from: {course.name}...")
                submissions_pl = course.get_multiple_submissions(
                    include=["assignment", 
                    "submission_comments", 
                    "course",
                    "user"],
                    student_ids="all"
                    )
                submissions = list(submissions_pl)
                submissions.sort(key=lambda x: x.workflow_state, reverse=True)

                print(f"Writing report entries for {course.name} ...")        
                write_course_headers(obj_report, course)

                for s in submissions:
                    write_submission_row(obj_report, s)
                
                write_course_footers(obj_report)

        runtime = round(date_delta(run_time_start))
        report_metrics = { 
                            "Version": version,
                            "Runtime (seconds)": runtime,
                            "Canvas URL": canvas_base_url
                        }

        end_report(obj_report, report_metrics)

        if flask_run:
            return filename
        else:
            webbrowser.open(filename,2)

if __name__ == "__main__":
    main()