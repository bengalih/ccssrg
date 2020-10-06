from datetime import datetime
import json
from ccssrg_classes import *

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
        else:
            selected_courses = userprefs.selected_courses

def write_prefs_file(userprefs):
    ''' Write user preferences to file '''
    filename = userprefs.file
    with open(filename, 'w') as f:
        json.dump(vars(userprefs), f)


def select_courses(courses, userprefs):
    ''' Selection prompt for courses to access '''
    try:
        with open(userprefs.file) as f:
            prefs = json.load(f)
            selected_courses = prefs['selected_courses']
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
            userprefs.selected_courses.append(c.id)
    elif choice == "":
        userprefs.selected_courses = selected_courses
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
                    userprefs.selected_courses = selected_courses

def friendly_time(timestamp, input_format=1, output_format=1):
    ''' Convert and return Canvas timestamps for easy display '''
    if output_format == 1:
        # For friendly comments
        time_format = '%m/%d/%Y (%a)'
    elif output_format == 2:
        # For report header
        time_format = '%A, %B %d %Y (%m/%d/%Y) %I:%M%p'

    try:
        if input_format == 1:
            timestamp = datetime.strptime(str(timestamp), "%Y-%m-%dT%H:%M:%SZ")
        timestamp = timestamp.strftime(time_format)
    except:
        pass
    else:
        return timestamp

def date_delta(timestamp, input_format=1, period="days"):
    ''' Find time difference from now for supplied Canvas time '''
    if input_format == 1:
        date_format = "%Y-%m-%dT%H:%M:%SZ"
        timestamp = datetime.strptime(timestamp, date_format)
    
    #timestamp = str(timestamp)
    delta = datetime.now() - timestamp

    if period == "days":
        return delta.days
    elif period == "seconds":
        return delta.seconds

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

def is_late(submission):
    ''' Determine if an unsubmitted submission is late based on due date'''
    s = submission
    if can_submit(s) and s.assignment['due_at']:
        if date_delta(s.assignment['due_at']) > 0:
            return True
        else:
            return False
    else:
        return False

def format_comments(comments, student_id):
    ''' Format found comments for HTML insertion '''
    f_com = ""
    if comments:
        for c in reversed(comments):
            css_class = []
            if c['author_id'] == student_id:
                css_class.append("student_comment")
            else:
                css_class.append("teacher_comment")

            if date_delta(c['created_at']) < 1:
                css_class.append("recent_comment")

            css_classes = " ".join(css_class)

            f_com=f"""
            						<div class="{css_classes}">
            							<li>
            								<span class="bold">{friendly_time(c['created_at'])}</span> 
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

        if date_delta(c['created_at']) < 7:
            recent_comments = True
    
    if recent_comments:
        return comments
    else:
        return None

       
def write_line(obj_report, line):
    ''' Writes line to report file '''
    #with open(filename, 'a+', encoding='utf-8') as f:
    obj_report.write(line)

def initialize_report(obj_report, user):
    ''' Create opening HTML/CSS for report '''
    f = obj_report

    html = f"""
    <HTML>
    <title>
        CCSSR - {user}
    </title>
    """
    write_line(f, html)

    # Append static HTML <head>/<style> (css)
    html_file = "ccssrg-head-css.html"
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
        		<h3>{friendly_time(datetime.now(), 0, 2)}</h3>
    		<div style="text-align: center">
    			<a href="#key">view report key</a>
    		</div>
    		<table>
    """
    write_line(f, html)

    return f

def write_course_headers(obj_report, course):
    ''' Write the ty rows for each course to HTML report '''
    f = obj_report
    html = f"""
    			<tr>
    				<th class=course colspan=7>
                        <a href={course.tabs[0]['full_url']} target=_blank>{course.name}</a>
                    </th>
    			</tr>
    			<tr>
    				<th>Course</th>
    				<th>Assignment</th>
    				<th>Assigned</th>
    				<th>Due</th>
    				<th>Status</th>
    				<th>Grade</th>
    				<th>Comments</th>
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

    # Tag suspicious entires with 'no submissions'
    if (
        s.workflow_state == "unsubmitted"
        and not s.assignment['has_submitted_submissions']
    ):
        tr_css_class.append("has_no_submissions")

    # Show all graded within 7 days
    if s.graded_at:
        if date_delta(s.graded_at) < 7:
            row_visible = True
            if date_delta(s.graded_at) < 3:
                td_status_css_class.append("graded_1")

    # Show all late
    if is_late(s) and not s.graded_at:
        row_visible = True
        td_status_css_class.append("is_late")
    
    # Show all with comments (from get_comments() < 7)
    comments = get_comments(s)
    if comments:
        row_visible = True
        comments = format_comments(comments, s.user['id'])
    else:
        comments = ""
    
    if row_visible:
        tr_css_class.append("show_in_report")

    tr_css_classes = " ".join(tr_css_class)
    td_status_css_classes = " ".join(td_status_css_class)
    submission_types = " ".join(s.assignment['submission_types'])

    # temporary fix to remove faulty iframes from description
    description = "No description provided.  Click on assignment link for more info (Canvas login required)."
    if s.assignment['description']:
        description = str.replace(s.assignment['description'], 'iframe', 'iframe(removed-by-code)')
        description = str.replace(description, "<img", "<br><img")

    html = f"""
    			<tr class=\"{tr_css_classes}\">
    				<td>{s.course['name']}</td>
    				<td>
    					<div class=\"tooltip\">
    						<a href=\"{s.assignment['html_url']}\" target=\"_blank\">{s.assignment['name']}</a>
    						<span class=\"ttt_assignment\">Submission Type(s):<br>{submission_types}</span>
    					</div>
    				<label class="btn" for="modal-{s.id}">DESCRIPTION</label>
					<input class="modal-state" id="modal-{s.id}" type="checkbox" />
					<div class="modal">
                        <label class="modal__bg" for="modal-{s.id}"></label>
                        <div class="modal__inner">
                            <label class="modal__close" for="modal-{s.id}"></label>
                            <h2><a href="{s.assignment['html_url']}" target="_blank">{s.assignment['name']}</a></h2>
                            <span class="submission_types">Submission Type(s):<br>{submission_types}</span>
                            {description}
                        </div>
					</div>
    				</td>
    				<td>{friendly_time(s.assignment['unlock_at'])}</td>
    				<td>{friendly_time(s.assignment['due_at'])}</td>
    				<td class=\"{td_status_css_classes}\">
    					<div class=\"tooltip\">{s.workflow_state.upper()}
    						<span class=\"ttt_status\">Submitted Date:<br>{friendly_time(s.submitted_at)}</span>
    					</div>
    				</td>
    				<td>
    					<div class=\"tooltip\">{get_grade(s)}
    						<span class=\"ttt_grade\">Graded Date:<br>{friendly_time(s.graded_at)}</span>
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
                <tr class="key">
                    <th class="key_title" colspan="7">REPORT DETAILS</th>
                </tr>
                <tr class="key">
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
                <tr class="key">
                    <th class="key_title" colspan="7">COLOR KEY</th>
                </tr>
                <tr class="key">
                    <th class="key submitted">SUBMITTED</th>
                    <th class="key unsubmitted">UNSUBMITTED</th>
                    <th class="key is_late">LATE</th>
                    <th class="key graded">GRADED</th>
                    <th class="key graded_1">GRADED</th>
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
            </tbody>
        </table>
        <br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>
    </div>
    <div class = "report_metrics">{report_metrics}</div>
</body>
</html>
"""
    write_line(f, html)
    obj_report.close()