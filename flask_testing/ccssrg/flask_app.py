from flask import Flask, request, send_file
from ccssrg_main import main

@app.route("/", methods=["GET", "POST"])

def canvas_report():
    if request.method == "POST":
        canvas_base_url = None
        access_token = None
        download_file = None
        course_list = []
        access_token = request.form["Access Token"]
        canvas_base_url = request.form["Canvas URL"]
        courses = request.form["Course List"]
        if len(courses) > 0:
            course_list = courses.split(",")
        download_file = 'Download' in request.form
        if access_token is not None:
            f = main("flask", access_token=access_token, canvas_base_url=canvas_base_url, course_list=course_list)
            if download_file:
                return send_file(f, as_attachment=True)
            else:
                return send_file(f)

    return '''
        <html>
            <head>
                <title>
                    CCSSRG
                </title>
                <style>
                    a {
                        color: gold;
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
                        background-color: #2D3B45;
                        color: white;
                        font-weight: bold;
                        padding: 100;
                        font-size: large;
                    }
                    .notes {
                        color: black;
                        background-color: yellow;
                        border: dotted;
                    }
                    .disclosures {
                        color: indianred;
                        font-size: small;
                        font-style: italic;
                    }
                </style>
            </head
            <body>
                <div class="content">
                    <h1>Canvas Consolidated Student Submissions Report Generator</h1>
                    <h2>version 0.5a</h2>
                    <form method="post" action=".">
                        <p>Enter your
                        <a target=_blank href="https://community.canvaslms.com/t5/Student-Guide/How-do-I-manage-API-access-tokens-as-a-student/ta-p/273">Access Token:</a></p>
                        <p><input name="Access Token" size="80" /></p>
                        <p>Enter Canvas URL (or use default):</p>
                        <p><input name="Canvas URL" size="30" value="https://tulsaps.instructure.com" /></p>
                        <p>Enter comma separated list of courses for report (leave empty for all courses):</p>
                        <p><input name="Course List" size="30" /></p>
                        <p><input name="Download" type="checkbox" id="Download" value="on" >
                        <label for="Download">Download report only?</label></p>
                        <p><input type="submit" value="RUN REPORT" /></p>
                        <span class="notes">(Please wait up to a minute for a standard report...)</span><br><br>
                        <span class="disclosures">* By submitting your Access Token for a report you will be transmitting it through 3rd party web services to request Canvas data.<br>
                        Access Tokens are not captured or stored.  Generated reports however may be accessible by server administrators.<br>
                        No access to Canvas is granted beyond what is required for the report to run upon submission.</span>
                    </form>
                </div>
            </body>
        </html>
    '''
if __name__ == "__main__":
    app.run()