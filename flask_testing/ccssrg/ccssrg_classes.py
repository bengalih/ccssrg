class UserPrefs:
    """ Represents user preferences for Canvas login"""

    def __init__(self):
        """Initialize name and age attributes"""
        self.canvas_url = "https://tulsaps.instructure.com"
        self.name = None
        self.token = None
        self.selected_courses = {}
        self.file = None