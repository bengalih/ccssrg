import json, os, pytz, re
from datetime import datetime, timezone

def prompt_creds(userprefs):
    ''' Prompt user for new access token '''
    token = ""
    while token == "":
        token = input("Please enter Canvas student token ('q' to quit):")
    
    if token == 'q':
        quit()
    else:
        userprefs.name = None
        userprefs.token = token

def access_prefs(userprefs):
    ''' Get saved user preferences/credentials from file '''
    try:
        with open(userprefs.file) as f:
            prefs = json.load(f)
            userprefs.name = prefs['name']
            userprefs.token = prefs['token']
    except:
        prefs = prompt_creds(userprefs)
    else:
        print(f"Found user: {userprefs.name}")
        prompt = input(f"Continue with this user? (y/n/q):")
        if prompt == "n":
            prefs = prompt_creds(userprefs)
        elif prompt == "q":
            quit()

def write_prefs_file(userprefs):
    ''' Write user preferences to file '''
    filename = userprefs.file
    with open(filename, 'w') as f:
        json.dump(vars(userprefs), f)

def select_observees(observees):
    user_list = []
    choice_list = list(range(1,len(list(observees))+1))
    observee_list = dict(zip(choice_list,observees))
    
    print("Found following observees:\n")
    for choice, user in observee_list.items():
        print(f"{choice}) {user.name} ({user.id})")

    choice = input(
        f"\nSelect number(s) from list (e.g.: 1,3,9,...)\n"
        f"- '*' for all\n"
        f"- 'q' to quit.\n\n"
        f"Enter List:")

    if choice.lower() == "q":
        quit()
    elif choice == "*":
        for o in observee_list:
            user_list.append(observee_list[o])
    else:
        selected_observees = choice.split(",")
        for c in selected_observees:
            try:
                c = int(c)
            except:
                print(f"{c} is invalid.  Removing from list...")
            else:
                if c in observee_list:
                    user_list.append(observee_list[c])
                else:
                    print(f"{c} is invalid.  Removing from list...")
        
    return user_list

def select_courses(user, courses, userprefs):
    ''' Selection prompt for courses to access '''
    try:
        with open(userprefs.file) as f:
            prefs = json.load(f)
            course_lists = prefs['selected_courses']
            selected_courses = course_lists.pop(user.name)
    except:
        selected_courses = []
    else:
        pass

    x = 0
    for course in courses:
        x += 1
        print(f"{x}) {course.name} ({course.id})")

    choice = input(
        f"\nSelect number(s) from list (e.g.: 1,3,9,...)\n"
        f"- '*' for all\n"
        f"- 'enter' for current list {selected_courses}\n"
        f"- 'q' to quit.\n\n"
        f"Enter List:")
    
    if choice == 'q':
        quit()
    elif choice == '*':
        for c in courses:
            selected_courses.append(c.id)
    elif choice == "":
        # selected_courses = selected_courses
        pass
    else:
        selected_courses = []
        user_range = choice.split(",")

        for c in user_range:
            try:
                c = int(c)
            except ValueError:
                print(f"{c} is invalid, and removed from list.")
                user_range = None
            else:
                if (int(c) < 1) or (int(c) > x):
                    print(f"{c} is out of range,and removed from list.")
                    user_range = None
                else:
                    if c not in selected_courses:
                        selected_courses.append(courses[c-1].id)
    
    course_lists[user.name] = selected_courses
    userprefs.selected_courses = course_lists
    return selected_courses

def now_utc():
    now_utc = datetime.now(tz=timezone.utc)
    return now_utc

def convert_to_utc(str_time):
    ''' convert naive UTC string to aware datetime object '''
    dt_format = "%Y-%m-%dT%H:%M:%SZ"
    utc_time = datetime.strptime(str_time, dt_format)
    utc_time = utc_time.replace(tzinfo=timezone.utc)
    return utc_time

def date_delta(dt_utc):
    ''' Determine time from supplied utc '''
    delta = now_utc() - dt_utc
    return delta.total_seconds()  

def time_localize_utc(dt_utc, timezone):
    ''' convert aware UTC object to course time_zone '''
    tz_data = timezone
    tz = pytz.timezone(tz_data)
    localized_time = dt_utc.astimezone(tz)
    return localized_time

def localized_time_str(str_utc, timezone):
    if str_utc:
        report_date_time = {}
        dt_utc = convert_to_utc(str_utc)
        localized_time = time_localize_utc(dt_utc, timezone)
        date_format = '%m/%d/%Y (%a)'
        time_format = '%I:%M:%S %p'
        date = localized_time.strftime(date_format)
        time = localized_time.strftime(time_format)
        return (date, time)
    else:
        return ("", "")

def can_submit(submission):
    ''' Determine if a specific submission is eligible to be submitted '''
    s = submission
    if (
        s.workflow_state == 'unsubmitted'
        and not s.assignment['locked_for_user']
        and "none" not in s.assignment['submission_types']
        and s.assignment['due_at']
    ):
        return True
    else:
        return False

def is_late(submission):
    ''' Determine if an unsubmitted submission is late based on due date'''
    s = submission
    if can_submit(s) and s.assignment['due_at']:
        utc_time = convert_to_utc(s.assignment['due_at'])
        return date_delta(utc_time) >= 0
    else:
        return False

def is_recent(utc_time, days):
    ''' Determine if date is within past 72 hours '''
    return date_delta(utc_time) < (days * 60 * 60 * 24)   

def get_grade(submission):
    ''' Get grade score for a graded assignment '''
    s = submission
    if s.graded_at:
        try:
            grade = round((s.score / s.assignment['points_possible']) * 100)
        except ZeroDivisionError:
            grade = 100
    else:
            grade = "-"
    return grade

def format_comments(comments, student_id, time_zone):
    ''' Format found comments for HTML insertion '''
    f_com = ""
    if comments:
        for c in reversed(comments):
            css_class = []
            if c['author_id'] == student_id:
                css_class.append("student_comment")
            else:
                css_class.append("teacher_comment")

            if is_recent(convert_to_utc(c['created_at']), 1):
                css_class.append("recent_comment")

            css_classes = " ".join(css_class)

            (date, time) = localized_time_str(c['created_at'], time_zone)

            f_com += f"""
            						<div class="{css_classes}">
            							<li>
            								<span class="bold">{date}</span> 
            								<span class="italic">{c['comment']}</span>
            							</li>
            						</div>
            """

        return f_com
    else:
        return f_com

def get_comments(submission):
    ''' Find comments eligible for insertion into report '''
    s = submission
    comments = []
    recent_comments = False
    for c in s.submission_comments:
        comment = {}
        comment = {
            "id": c['id'],
            "comment": c['comment'],
            "created_at": c['created_at'],
            "author_id": c['author_id'],
            "author_name": c['author_name']
        }
        comments.append(comment)

        if is_recent(convert_to_utc(c['created_at']), 7):
            recent_comments = True
    
    if recent_comments:
        return comments
    else:
        return None
       
def write_line(obj_report, line):
    ''' Writes line to report file '''
    #with open(filename, 'a+', encoding='utf-8') as f:
    obj_report.write(line)

def initialize_report(obj_report, user, report_time):
    ''' Create opening HTML/CSS for report '''
    f = obj_report
    time_header = report_time.strftime("%m/%d/%Y %I:%M %p")
    html = f"""
    <HTML>
    <title>
        CCSSR - {user}
    </title>
    """
    write_line(f, html)

    # Append static HTML <head>/<style> (css)
    script_path = os.path.dirname(__file__)
    html_file = os.path.join(script_path, 'ccssrg-head-css.html')
    with open(html_file, 'r') as h:
        html = h.read()
    write_line(f, html)

   # Append dyamic HTML body headers
    html = f"""
    <body>
    	<a name="top"></a>
    	<div class="content">
    		<h1>Canvas Colsolidated Student Submissions Report</h1>
    		<h2>{user}</h2>
        		<h3>{time_header}</h3>
    		<div class="report_link">
    			<a href="#key">view report key</a>
    		</div>
    """
    write_line(f, html)

    return f

def write_inbox(obj_report, user, time_zone, inbox_messages, canvas_url):
    f = obj_report
    num_of_messages=len(list(inbox_messages))
    message_list = ""

    if num_of_messages > 0:
        inbox_color="red"
        mail_message=f"You've got mail!({num_of_messages})"
        for message in inbox_messages:
            (message_date,
            message_time) = localized_time_str(message.last_message_at, time_zone)
            from_user = ""

            for p in message.participants:
                if p['id'] != user.id:
                    from_user = p['name']
            
            message_list += f"""
                    <li>
                        <span class="bold">FROM: </span>
                        {from_user}<br>
                        <span class="bold">TIME: </span>
                        {message_date} at {message_time}<br>
                        <span class="bold">SUBJECT: </span>
                        <span class="italic">{message}</span><br>        
                    </li>\n
                    <br>
        """
        message_list = f"""
                    <ul>
                        {message_list}
                    </ul>
        """
    else:
        inbox_color="#6e2b70"
        mail_message=""
        message_list="""
                    <div style="font-style: italic; text-align: center">
                        No unread messages
                    </div>
        """

    html=f"""
            <div class="inbox">
                <span style="color: {inbox_color};">
                {mail_message}
                <label class="mail_btn" for="modal-mail">
                    <svg width="36" height="37" class="ic-icon-svg ic-icon-svg--dashboard" viewBox="0 0 36 37" xmlns="http://www.w3.org/2000/svg">
                        <title>icon-inbox</title>
                        <path d="M3 17.962V0h30v17.962l-9.2 6.016-3.288-2.17c-1.39-.915-3.636-.914-5.024 0L12.2 23.98 3 17.962zM0 35l16.34-10.893c.916-.61 2.41-.607 3.32 0L36 35v2H0v-2zm36-16v13l-10-6.5L36 19zM0 19v13l10-6.5L0 19zM8 6c0-.552.456-1 .995-1h8.01c.55 0 .995.444.995 1 0 .552-.456 1-.995 1h-8.01A.995.995 0 0 1 8 6zm0 5c0-.552.455-1 .992-1h18.016c.548 0 .992.444.992 1 0 .552-.455 1-.992 1H8.992A.993.993 0 0 1 8 11zm0 5c0-.552.455-1 .992-1h18.016c.548 0 .992.444.992 1 0 .552-.455 1-.992 1H8.992A.993.993 0 0 1 8 16z" fill="currentColor" fill-rule="evenodd"></path>
                    </svg>
                </label>
                </span>
                <input class="modal-state" id="modal-mail" type="checkbox" />
                <div class="modal">
                    <label class="modal__bg" for="modal-mail"></label>
                    <div class="modal__inner">
                        <label class="modal__close" for="modal-mail"></label>
                        <h2>
                            <a href="{canvas_url}/conversations#filter=type=none" target="_blank">
                                Inbox Messages
                            </a>
                        </h2>
                        {message_list}
                    </div>
                </div>
            </div>
            <br>
    """
    write_line(f, html)

def write_course_headers(obj_report, course):
    ''' Write the ty rows for each course to HTML report '''
    f = obj_report
    grades_url = course.tabs[0]['full_url']
    x = re.search(".*\/courses\/[0-9]*", grades_url)
    grades_url = x.group() + "/grades/"
    # if course.enrollments['computed_current_score']:
    # print(course.enrollments)
    # quit()
    if course.enrollments[0]['computed_current_score']:
        course_score = f"({course.enrollments[0]['computed_current_score']}%)"
    else:
        course_score = ""

    html = f"""
            <table>
                <colgroup>
                    <col style="width: 110px;">
                    <col style="width: 140px;">
                    <col style="width: 100px;">
                    <col style="width: 100px">
                    <col style="width: 115px">
                    <col style="width: 75px">
                    <col style="width: 320px">
                </colgroup>
     			<tr>
    				<th class="main_header" colspan=7>
                        <a href="{course.tabs[0]['full_url']}" target="_blank">
                            {course.name} 
                            {course_score}
                        </a>
                    </th>
    			</tr>
    			<tr>
    				<th class="sub_header">Course</th>
    				<th class="sub_header">Assignment</th>
    				<th class="sub_header">Assigned</th>
    				<th class="sub_header">Due</th>
    				<th class="sub_header">Status</th>
    				<th class="sub_header">
                        <a href="{grades_url}" target="_blank">
                            Grade
                        </a>
                    </th>
                    <th class="sub_header">Comments</th>
    			</tr>
    """
    write_line(f, html)

def write_submission_row(obj_report, s):
    ''' Calculate classes for each submission and
    Write HTML into report for each submission '''

    f = obj_report
    tr_css_class = ["submission"]
    td_status_css_class = [s.workflow_state]

    row_visible = False

    # Show all unsubmitted
    if can_submit(s):
        row_visible = True

    # Tag suspicious(?) entires with 'no submissions'
    if (
        s.workflow_state == "unsubmitted"
        and not s.assignment['has_submitted_submissions']
    ):
        tr_css_class.append("has_no_submissions")

    # Show all graded within 7 days
    if s.graded_at:
        if date_delta(convert_to_utc(s.graded_at)) < 7:
            row_visible = True
            if date_delta(convert_to_utc(s.graded_at)) < 3:
                td_status_css_class.append("graded_recent")

    # Show all late
    if is_late(s) and not s.graded_at:
        row_visible = True
        td_status_css_class.append("is_late")
    
    # Show all with comments (from get_comments() < 7)
    comments = get_comments(s)
    if comments:
        row_visible = True
        comments = format_comments(comments, s.user['id'], s.course['time_zone'])
    else:
        comments = ""
    
    if row_visible:
        tr_css_class.append("show_in_report")

    tr_css_classes = " ".join(tr_css_class)
    td_status_css_classes = " ".join(td_status_css_class)
    submission_types = " ".join(s.assignment['submission_types'])

    tz = s.course['time_zone']
    (unlock_at_date,
       unlock_at_time) = localized_time_str(s.assignment['unlock_at'], tz)
    (due_at_date,
        due_at_time) = localized_time_str(s.assignment['due_at'], tz)
    (submitted_at_date,
       submitted_at_time) = localized_time_str(s.submitted_at, tz)
    (graded_at_date,
        graded_at_time) = localized_time_str(s.graded_at, tz)

    # temporary fix to remove faulty iframes from description
    description = "No description provided.  Click on assignment link for more info (Canvas login required)."
    if s.assignment['description']:
        description = str.replace(s.assignment['description'], 'iframe', 'iframe(removed-by-code)')
        description = str.replace(description, "<img", "<br><img")

    if s.preview_url:
        txt = s.preview_url
        x = re.search(f".*{s.user['id']}", txt)
        preview_url = x.group()

    html = f"""
    			<tr class="{tr_css_classes}">
    				<td>
                        <span class="small_font">
                            {s.course['name']}
                        </span>
                    </td>
    				<td>
                        <div class="tooltip">
    						<a class="course" href="{s.assignment['html_url']}" target="_blank">
                                {s.assignment['name']}
                            </a>
    						<span class="ttt_assignment">
                                Submission Type:<br>{submission_types}
                            </span>
    					</div>
    				<label class="btn" for="modal-{s.id}">DESCRIPTION</label>
					<input class="modal-state" id="modal-{s.id}" type="checkbox" />
					<div class="modal">
                        <label class="modal__bg" for="modal-{s.id}"></label>
                        <div class="modal__inner">
                            <label class="modal__close" for="modal-{s.id}"></label>
                            <h2>
                                <a href="{s.assignment['html_url']}" target="_blank">
                                    {s.assignment['name']}
                                </a>
                            </h2>
                            <span class="submission_types">
                                Submission Type(s):<br>{submission_types}
                            </span>
                            {description}
                        </div>
					</div>
    				</td>
                    <td>
                        <div class="tooltip">{unlock_at_date}
    						<span class="ttt_date">
                                Assigned Time:<br>{unlock_at_time}
                            </span>
    					</div>
                    </td>
                    <td>
                        <div class="tooltip">{due_at_date}
    						<span class="ttt_date">
                                Due Time:<br>{unlock_at_time}
                            </span>
    					</div>
                    </td>
    				<td class="{td_status_css_classes}">
    					<div class="tooltip">
                            <a href="{preview_url}" target="_blank">
                                {s.workflow_state.upper()} 
                            </a>
    						<span class="ttt_status">
                                Submitted Date:<br>{submitted_at_date}<br>
                                <span class="xx_small_font">
                                    {submitted_at_time}
                                </span>
                            </span>
    					</div>
    				</td>
    				<td>
    					<div class="tooltip">
                            {get_grade(s)}
    						<span class="ttt_grade">
                                Graded Date:<br>{graded_at_date}<br>
                                <span class="xx_small_font">
                                    {graded_at_time}
                                </span>
                            </span>
    					</div>
    				</td>
    				<td>
    					<ul>
                            {comments}
    					</ul>
    				</td>
                </tr>
"""
    write_line(f, html)

def write_course_footers(obj_report):
    html="""
                <tr>
                    <th class="main_footer" colspan=7>
                </tr>
            </table>
            <br><br>"""
    write_line(obj_report,html)

def end_report(obj_report, report_metrics):
    ''' Write closing HTML after processing and close file '''
    f = obj_report
    # Legend
    html = f"""
        </table>
        <br><br><br>
        <a name="key"></a>
        <div style="text-align: center">
            <a href="#top">back to top</a>
        </div>
        <table class="key">
            <tbody>
                <tr>
                    <th class="key_main_header" colspan="7">REPORT DETAILS</th>
                </tr>
                <tr>
                    <td class="report_details" colspan="7">
                        Report shows:
                        <ul>
                            <li>All UNSUBMITTED/LATE assignments that are accepting submissions
                            <li>All assignments graded within the last 7 days (< 3 days are color coded)
                            <li>All assignments with comments within the last 7 days (< 1 days are color coded)
                            <li>Hover over some table cells to see additional data (submission types, dates, etc..)
                        </ul>
                    </td>
                </tr>
                <tr>
                    <th class="key_sub_header" colspan="7">COLOR KEY</th>
                </tr>
                <tr>
                    <th class="key submitted">SUBMITTED</th>
                    <th class="key unsubmitted">UNSUBMITTED</th>
                    <th class="key is_late">LATE</th>
                    <th class="key graded">GRADED</th>
                    <th class="key graded_recent">GRADED</th>
                    <th class="key comments">COMMENTS</th>
                    <th class="key has_no_submissions">NO SUBMISSIONS</th>
                </tr>
                <tr class="key">
                    <td class="key">Submitted assignments are not shown unless other criteria are met</td>
                    <td class="key">All unsbmitted assignments</td>
                    <td class="key">All assignments past due date</td>
                    <td class="key">Graded within the past 7 days</td>
                    <td class="key">Graded within the past 3 days</td>
                    <td class="key">Comments from the past 7 days</br>
                    <span class="recent_comment">
                    - Comments made within past day<br>
                    </span>
                    <span class="teacher_comment">
                    - Comments from teacher
                    </span>
                    </td>
                    <td class="key">Special case where no submissions exist (invalid or submitted in external tool)</td>
                </tr>
                <tr>
                    <th class="key_sub_header" colspan="7">TIPS & TRICKS</th>
                </tr>
                <tr>
                    <td colspan="7">
                        <ul>
                            <li>Click on inbox to view unread messages and open Canvas Inbox
                            <li>Click on main header for each course to open course in Canvas
                            <li>Click on Grade header for each course to open grades in Canvas
                            <li>Click on Assignment names to open in Canvas
                            <li>Click on Assignment Description box for summary of assignment
                            <li>Click on Status to open Submission Details (comments/grade) in Canvas
                            <li>Hover over Assigned/Due/Status/Grade for more date/time information
                        </ul>
                    </td>
                </tr>  
                <tr>
                    <th class="key_footer" colspan="7"></th>
                </tr>              
            </tbody>
        </table>
        <br><br><br><br><br><br><br><br><br><br>
        <br><br><br><br><br><br><br><br><br><br>
        <br><br><br><br><br><br><br><br><br><br>
    </div>
    <div class = "report_metrics">{report_metrics}</div>
</body>
</html>
"""
    write_line(f, html)
    obj_report.close()