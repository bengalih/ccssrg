from datetime import datetime
import webbrowser
from canvasapi import Canvas, exceptions
from ccssrg_functions import *
from ccssrg_classes import *

PROD_URL = "https://tulsaps.instructure.com"

def main():
    version = "0.5b"
    start_time = datetime.now()

    userprefs = UserPrefs()
    userprefs.canvas_url = PROD_URL
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

    user_list = []
    user_list.append(user)

    for user in user_list:

        print(f"Setting up reporting environment...\n")
        date_time = start_time.strftime("%Y%m%d-%H%M%S")
        filename = f"{user.name}_{date_time}.html"
        obj_report = open(filename, 'a+', encoding='utf-8') 
        initialize_report(obj_report, user.name) 

        print(f"Accessing Canvas for Courses for: {user.name} (may take a moment)...\n")
        courses = canvas.get_courses(
            state=["available"], enrollment_state="active", include=["tabs"])
        
        if courses:
            select_courses(courses, userprefs)
            
            ''' Write preference to file after course selection '''
            write_prefs_file(userprefs)

            for course in courses:
                if course.id in userprefs.selected_courses:
                    print(f"Accessing Canvas for assigments from: {course.name}...")
                    submissions_pl = course.get_multiple_submissions(
                        include=["assignment", 
                        "submission_comments", 
                        "course",
                        "user"],
                        student_ids=["all"]
                        )
                    submissions = list(submissions_pl)
                    submissions.sort(key=lambda x: x.workflow_state, reverse=True)

                    print(f"Writing report entries for {course.name} ...")        
                    write_course_headers(obj_report, course)

                    for s in submissions:
                        write_submission_row(obj_report, s)

    runtime = date_delta(start_time, 0, "seconds")

    report_metrics = { 
                        "Version": version,
                        "Runtime (seconds)": runtime,
                        "Canvas URL": PROD_URL
                    }

    end_report(obj_report, report_metrics)
    webbrowser.open(filename,2)

if __name__ == "__main__":
    main()