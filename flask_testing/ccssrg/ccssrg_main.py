import os, webbrowser
from datetime import datetime
from pathlib import Path
from canvasapi import Canvas, exceptions
from ccssrg_functions import *
from ccssrg_classes import *

CANVAS_URL = "https://tulsaps.instructure.com"

def main(run_method, **kwargs):
    version = "0.6b"

    if run_method == "local":
        userprefs = UserPrefs()
        userprefs.canvas_url = CANVAS_URL
        userprefs.file = "prefs.json"

        while True:
            try:
                prefs = access_prefs(userprefs)
                canvas = Canvas(userprefs.canvas_url, userprefs.token)
                user = canvas.get_current_user()
                userprefs.name = user.name
            except exceptions.InvalidAccessToken as e:
                print(e.message[0]['message'])
                print("Authorization Failure. Is your token correct?")
            else:
                print(f"Successfully connected for {user.name} ({user.id})")
                break
        
        observees = user.get_observees()
        if (len(list(observees))) > 0:
            user_list = select_observees(observees)
        else:
            user_list = []
            user_list.append(user)
    else:
        canvas_base_url = kwargs.get('canvas_base_url', None)
        token = kwargs.get('token', None)
        course_list = kwargs.get('course_list', None)
        canvas_base_url = "https://canvas.instructure.com"
        token = "7~WG2Im7Ze88xO9BLgU8MF7vmv5QADrVmuXgik1H6doOr3VoT68uKhd3Z3iViWCymO"
        canvas = Canvas(canvas_base_url, token)
        user_list = []
        user_list.append(canvas.get_current_user())
        
    for user in user_list:
        print(f"Setting up reporting environment...\n")
        print(f"!!!!!!!!!! {__name__ }")
        report_time = datetime.now()
        report_time_file = report_time.strftime("%Y%m%d-%H%M%S")
        
        if run_method == "local":
            script_path = os.path.dirname(__file__)
            reports_path = os.path.join(script_path, 'reports')
            Path("reports_path").mkdir(parents=True, exist_ok=True)
            filename = f"{reports_path}/{user.name}_{report_time_file}.html"
        else:
            # filename = f"/home/ccssrg/prod/reports/" \
            #     f"{user.name}_{report_time_file}.html"
            filename = f"{user.name}_{report_time_file}.html"

        obj_report = open(filename, 'a+', encoding='utf-8') 
        initialize_report(obj_report, user.name, report_time) 

        print(f"Accessing Canvas for Courses for: {user.name} (may take a moment)...\n")
        courses = user.get_courses(
            state=["available"], enrollment_state="active",
            include=["tabs", "total_scores"]
            )
        
        if courses:
            if run_method == "local":
                selected_courses = select_courses(user, courses, userprefs)
                ''' Write preference to file after course selection '''
                write_prefs_file(userprefs)
            else:
                selected_courses = course_list
                #for c in courses:
                    #selected_courses.append(c.id)

            run_time_start = now_utc()

            for course in courses:
                # Check if account is observer/observed account
                # and scope only for each user.
                if hasattr(user, 'observation_link_root_account_ids'):
                    student_ids = user.id
                else:
                    student_ids = "all"

                if course.id in selected_courses:
                    print(f"Accessing Canvas for assigments from: {course.name}...")
                    submissions_pl = course.get_multiple_submissions(
                        include=["assignment", 
                        "submission_comments", 
                        "course",
                        "user"],
                        student_ids=[student_ids]
                        # student_ids=["all"]
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
                                "Canvas URL": CANVAS_URL
                            }

            end_report(obj_report, report_metrics)
            webbrowser.open(filename,2)