import unittest
# from server import app
from model import db, connect_to_db #ALSO LIST NAME OF FUNCTIONS TO TEST
import server 

class TestMyPillHelper(unittest.TestCase):

    def setUp(self):
        """Code to run before every test."""

        self.client = server.app.test_client()
        server.app.config['TESTING'] = True

    def homepage_rendering(self):

        result = self.client.get("/")
        self.assertIn(b"Pill Helper", result.data)

    def search_bar_rendering(self):
        pass

    def search_results_rendering(self):
        pass

    def more_info_rendering(self):
        pass

    def register_new_user(self):
        pass



if __name__ == "__main__":
    unittest.main()