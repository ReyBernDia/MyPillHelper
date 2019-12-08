import unittest
from server import app
from test_model import db, connect_to_db #ALSO LIST NAME OF FUNCTIONS TO TEST
import server 

class TestMyPillHelper(unittest.TestCase):

    def setUp(self):
        """Code to run before every test."""

        self.client = server.app.test_client()
        server.app.config['TESTING'] = True

    def test_homepage_rendering(self):
        """Can we reach the homepage?"""

        result = self.client.get("/")
        self.assertIn(b"Pill Search", result.data)

    def test_find_meds_rendering(self):
        """Are you able to enter in items to search for a pill."""

        result = self.client.get("/find_meds")
        self.assertIn(b"How to identify", result.data)

    def test_search_results_rendering(self):
        """Do search results render after entering find-med info."""

        identify_info = {'pill_imprint': "APO", 'pill_shape': "Capsule"}

        result = self.client.post("/results", data=identify_info,
                                  follow_redirects=True)

    def test_more_info_rendering(self):
        """Can you see more information about selected medication."""

        result = self.client.get("/more_info/Risperidone")
        self.assertIn(b"More Information on Your", result.data)

    def test_register_page(self):
        """Can you see the registration page."""

        result = self.client.get("/register")
        self.assertIn(b"Registration", result.data)

    def test_render_login(self):
        """Can see login page."""

        result = self.client.get("/login")
        self.assertIn(b"LOG IN", result.data)



if __name__ == "__main__":
    unittest.main()