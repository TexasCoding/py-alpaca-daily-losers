import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry


class Requests:
    def __init__(self) -> None:
        self.retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        self.adapter = HTTPAdapter(max_retries=self.retry_strategy)
        self.session = requests.Session()
        self.session.mount("https://", self.adapter)
        self.session.mount("http://", self.adapter)
        self.headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "en-US,en;q=0.9",
            "referer": "https://www.google.com",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, \
                like Gecko) Chrome/85.0.4183.83 Safari/537.36 Edg/85.0.564.44",
        }

    def _issue_request(
        self,
        method: str,
        url: str,
    ):
        """
        Args:
            method: A string representing the HTTP method to be used in the
            request.
            url: A string representing the URL to send the request to.
            headers: An optional dictionary containing the headers for the
            request.
            params: An optional dictionary containing the query parameters for
            the request.
            json: An optional dictionary containing the JSON payload for the
            request.

        Returns:
            The response object returned by the server.

        Raises:
            Exception: If the response status code is not one of the
            acceptable statuses (200, 204, 207).
        """
        response = self.session.request(
            method=method,
            url=url,
            headers=self.headers,
        )
        acceptable_statuses = [200, 204, 207]
        if response.status_code not in acceptable_statuses:
            raise Exception(f"Request Error: {response.text}")
        return response

    def get(
        self,
        url: str,
    ):
        """
        Args:
            url: A string representing the URL to make a GET request to.
            headers: An optional dictionary containing headers to include in
            the request.
            params: An optional dictionary containing query parameters to
            include in the request.

        Returns:
            The response from the GET request.
        """
        return self._issue_request(
            "GET",
            url,
        )

    def post(
        self,
        url: str,
    ):
        """
        Sends a POST request to the specified URL with optional headers and
        payload.

        Args:
            url (str): The URL to which the POST request will be sent.
            headers (Dict[str, str], optional): Dictionary of headers to
            include in the request. Defaults to None.
            payload (Dict[str, str], optional): Dictionary of data to be sent
            as the payload of the request. Defaults
            to None.

        Returns:
            The response of the POST request.
        """
        return self._issue_request(
            "POST",
            url,
        )

    def delete(
        self,
        url: str,
    ):
        """
        Args:
            url: The URL of the endpoint to send the DELETE request to.
            headers: (optional) A dictionary of headers to be included in the
            request.
            params: (optional) A dictionary of query string parameters to be
            included in the request.

        Returns:
            The response from the DELETE request.

        Raises:
            Any exceptions raised during the request.
        """
        return self._issue_request(
            "DELETE",
            url,
        )

    def request(
        self,
        method: str,
        url: str,
    ):
        """
        Args:
            method: The HTTP method to use for the request
            (e.g., 'GET', 'POST', 'PUT', etc.).
            url: The URL to send the request to.
            headers: Optional. A dictionary of HTTP headers to include in the
            request.
            json: Optional. A dictionary of JSON data to include in the
            request body.
            params: Optional. A dictionary of query parameters to include in
            the request URL.

        Returns:
            The response from the server.
        """
        return self._issue_request(
            method,
            url,
        )
