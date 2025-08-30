import logging
import requests
from requests.auth import HTTPBasicAuth
import json

class IntegrationAgentPMT:
    """
    Agent for communicating with an external Project Management Tool (PMT) like Jira.
    """
    def __init__(self, provider: str, url: str, username: str, api_token: str):
        if not all([provider, url, username, api_token]):
            raise ValueError("All integration parameters (URL, Username, API Token) are required.")

        self.provider = provider
        # Ensure URL is formatted correctly for the API
        self.base_url = f"https://{url}" if not url.startswith("http") else url
        self.auth = HTTPBasicAuth(username, api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        logging.info(f"IntegrationAgentPMT initialized for provider '{self.provider}' at URL '{self.base_url}'")

    def _extract_text_from_adf(self, adf_node):
        """Recursively extracts all text from a Jira ADF node."""
        text_parts = []
        if adf_node.get("type") == "text":
            return adf_node.get("text", "")

        if "content" in adf_node and isinstance(adf_node["content"], list):
            for child_node in adf_node["content"]:
                text_parts.append(self._extract_text_from_adf(child_node))

        # Add newlines between paragraphs and other block elements for readability
        if adf_node.get("type") in ["paragraph", "heading"]:
            return "".join(text_parts) + "\n"

        return "".join(text_parts)

    def search_issues(self, query: str) -> list:
        """
        Searches for issues using the tool's query language (e.g., JQL for Jira).
        """
        # This endpoint is specific to Jira's REST API v3.
        api_url = f"{self.base_url}/rest/api/3/search"

        payload = json.dumps({
            "jql": query,
            "fields": ["summary", "description", "status"] # Request specific fields
        })

        logging.info(f"--- JIRA API REQUEST ---")
        logging.info(f"URL: POST {api_url}")
        logging.info(f"Payload: {payload}")
        logging.info(f"------------------------")

        try:
            response = requests.post(api_url, data=payload, headers=self.headers, auth=self.auth, timeout=30)

            logging.info(f"--- JIRA API RESPONSE ---")
            logging.info(f"Status Code: {response.status_code}")
            logging.info(f"Response Body: {response.text}")
            logging.info(f"-------------------------")

            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

            issues = response.json().get('issues', [])
            formatted_issues = []
            for issue in issues:
                fields = issue.get('fields', {})
                # Jira's new description format is complex; we'll extract the plain text.
                description_text = "No description."
                if fields.get('description'):
                    try:
                        # Use the new helper method to parse the entire ADF structure
                        full_description = self._extract_text_from_adf(fields['description']).strip()
                        if full_description:
                            description_text = full_description
                    except Exception as e:
                        logging.error(f"Failed to parse ADF description for issue {issue.get('key')}: {e}")
                        description_text = "Could not parse description."

                formatted_issues.append({
                    'id': issue.get('key'),
                    'title': fields.get('summary'),
                    'description': description_text,
                    'status': fields.get('status', {}).get('name')
                })
            return formatted_issues

        except requests.exceptions.Timeout:
            logging.error(f"API request timed out when searching issues.")
            raise ConnectionError("The request to the integration endpoint timed out.")
        except requests.exceptions.RequestException as e:
            logging.error(f"API request to search issues failed: {e}")
            raise ConnectionError(f"Failed to connect to the integration endpoint. Check URL and credentials. Details: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred during issue search: {e}")
            raise

    def create_issue(self, title: str, description: str, project_key: str, issue_type_id: str) -> dict:
        """
        Creates a new issue in the external tool (specifically Jira).

        Returns:
            A dictionary containing the new issue's 'key' and 'url'.
        """
        api_url = f"{self.base_url}/rest/api/3/issue"

        # Jira uses a complex document format (ADF) for multi-line descriptions
        description_payload = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": description if description else "No description provided."
                        }
                    ]
                }
            ]
        }

        payload = json.dumps({
            "fields": {
                "project": {"key": project_key},
                "summary": title,
                "issuetype": {"id": issue_type_id},
                "description": description_payload
            }
        })

        logging.info(f"--- JIRA API REQUEST (CREATE) ---")
        logging.info(f"URL: POST {api_url}")
        logging.info(f"Payload: {payload}")
        logging.info(f"---------------------------------")

        try:
            response = requests.post(api_url, data=payload, headers=self.headers, auth=self.auth, timeout=30)

            logging.info(f"--- JIRA API RESPONSE (CREATE) ---")
            logging.info(f"Status Code: {response.status_code}")
            logging.info(f"Response Body: {response.text}")
            logging.info(f"----------------------------------")

            response.raise_for_status()

            response_data = response.json()
            new_issue_key = response_data.get('key')
            new_issue_url = response_data.get('self')

            if not new_issue_key or not new_issue_url:
                raise ValueError("API response did not contain the new issue's key or URL.")

            return {"key": new_issue_key, "url": new_issue_url}

        except requests.exceptions.RequestException as e:
            error_details = str(e)
            try:
                # Try to parse a more helpful error message from Jira's response
                error_json = e.response.json()
                error_messages = error_json.get('errorMessages', [])
                errors = error_json.get('errors', {})
                if error_messages:
                    error_details = ". ".join(error_messages)
                elif errors:
                    # Concatenate field-specific errors
                    error_details = ". ".join([f"{field}: {message}" for field, message in errors.items()])
            except Exception:
                pass # Stick with the original exception string

            logging.error(f"API request to create issue failed: {error_details}")
            raise ConnectionError(f"Failed to create issue. Please check your Project Key and Issue Type ID in Project Settings. Details: {error_details}")
        except Exception as e:
            logging.error(f"An unexpected error occurred during issue creation: {e}")
            raise