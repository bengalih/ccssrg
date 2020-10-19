from flask import Flask, request, send_file
from ccssrg_functions import main

app = Flask(__name__)
app.config["DEBUG"] = True

VERSION = "0.6c"

@app.route("/", methods=["GET", "POST"])

def canvas_report():
    if request.method == "POST":
        canvas_base_url = None
        access_token = None
        download_file = None
        selected_courses = []
        access_token = request.form["Access Token"]
        canvas_base_url = request.form["Canvas URL"]
        courses = request.form["Course List"]
        if len(courses) > 0:
            course_input = courses.split(",")
            selected_courses = []
            for course in course_input:
                try:
                    course=int(course)
                    selected_courses.append(course)
                except:
                    pass   #not an int
        download_file = 'Download' in request.form
        if access_token is not None:
            f = main(flask=True,access_token=access_token, canvas_base_url=canvas_base_url, selected_courses=selected_courses)
            if download_file:
                return send_file(f, as_attachment=True)
            else:
                return send_file(f)

    html = '''
        <html>
            <head>
                <title>
                    CCSSRG
                </title>
                <style>
                    a {
                        color: #c84114;
                    }
                    h1 {
                        font-size: xx-large;
                    }
                    h2 {
                        font-size: x-small;
                    }
                    .content {
                        max-width: 960px;
                        margin: auto;
                        text-align: center;
                        background-color: white;
                        color: #2D3B45;
                        font-weight: bold;
                        padding: 25;
                        font-size: large;
                        font-family: "Lato Extended","Lato","Helvetica Neue",Helvetica,Arial,sans-serif;
                        border: 20px solid #6e2b70;
                        border-radius: 20px;
                    }
                    .notes {
                        color: yellow;
                        background-color: #6e2b70;
                        font-style: italic;
                        padding: 10;
                        border-radius: 20px;
                    }
                    .disclosures {
                        color: #c84114;
                        font-size: small;
                        font-style: italic;
                    }
                    .footer {
                        text-align: center;
                        color: #c84114;
                        font-size: small;
                        font-style: italic;
                    }
                    .italic{
                        text-align: center;
                        font-size: small;
                        font-style: italic;
                    }
                </style>
            </head>
            <body>
                <div class="content">
                    <h1>Canvas Consolidated Student Submissions Report Generator</h1>
    '''
    html += f'''
                    <h2>version {VERSION}</h2>
            '''
    html += '''
                    <form method="post" action=".">
                        <a href="help.html#Access_Token">Access Token:</a><br>
                        <span class="italic">(required)</span>
                        <p><input name="Access Token" size="80" /></p>
                        <a href="help.html#Canvas_URL">Canvas URL:</a><br>
                        <span class="italic">(change for your institution)</span>
                        <p><input name="Canvas URL" size="30" value="tulsaps.instructure.com" /></p>
                        <a href="help.html#Course_List">Course List:</a><br>
                        <span class="italic">(leave empty for all courses)</span>
                        <p><input name="Course List" size="30" /></p>
                        <p><input name="Download" type="checkbox" id="Download" value="on" >
                        <label for="Download">
                            <a href="help.html#Download_Only">
                                Download report only
                            </a>
                        </label></p>
                        <p><input type="submit" value="RUN REPORT" /></p>
                        <span class="notes">(Please wait up to a minute for report generation.)</span><br><br>
                        <span class="disclosures">* By submitting your Access Token for a report you will be transmitting it through 3rd party web services to request Canvas data.<br>
                        Access Tokens are not captured or stored.  Generated reports however may be accessible by server administrators.<br>
                        No access to Canvas is granted beyond what is required for the report to run upon submission.
                        <br>
                        *<a href="help.html#More_Info">more info</a>
                        </span>
                    </form>
                </div>
                <div class="footer"><a target="_blank" href="https://github.com/bengalih/ccssrg">ccssrg on github</a></div>
            </body>
        </html>
    '''

    return html

@app.route("/help.html", methods=["GET"])

def show_help():
    return send_file("help.html")