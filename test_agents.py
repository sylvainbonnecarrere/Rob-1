import unittest
from unittest.mock import patch
from agents import tester_agent

class TestAgentFunctionality(unittest.TestCase):
    def test_tester_agent_success(self):
        agent_config = {
            "api_url": "http://localhost:5001/",
        }
        payload = {"key": "value"}

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"result": "success"}

            result = tester_agent(agent_config, payload)
            self.assertEqual(result, {"result": "success"})

    def test_tester_agent_failure(self):
        agent_config = {
            "api_url": "http://localhost:5001/",
        }
        payload = {"key": "value"}

        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 500
            mock_post.return_value.text = "Internal Server Error"

            result = tester_agent(agent_config, payload)
            self.assertEqual(result, {"erreur": "Code HTTP 500"})

if __name__ == "__main__":
    unittest.main()