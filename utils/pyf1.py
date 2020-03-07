import urllib
import logging

from rauth import OAuth1Session, OAuth1Service
from base64 import b64encode

logger = logging.getLogger()


class F1API(OAuth1Session):
    """A class for initializaint the F1 api session"""

    def __init__(self, clientKey, clientSecret, username, password):
        """Class Constructor assigns class variables and attempts authentication

        :param clientKey: Oauth1 client key
        :type clientKey: string
        :param clientSecret: Oauth1 client secret
        :type clientSecret: string
        :param username: FellowshipOne username
        :type username: string
        :param password: FellowshipOne password :type password: string"""

        # CT fellowshipone base URL
        self.baseUrl = "https://christny.fellowshiponeapi.com"

        # Hash credentials
        credential_string = "{} {}".format(username, password)
        credentials = b64encode(bytes(credential_string, "utf-8"))
        credentials = urllib.parse.quote_plus(credentials)

        # Setup OAuth1 Service to retrive Request Tokens
        service = OAuth1Service(
           consumer_key=clientKey,
           consumer_secret=clientSecret,
           request_token_url="%s/v1/PortalUser/AccessToken" % self.baseUrl
        )

        # Fetch tokens from fellowship one
        tokens = service.get_raw_request_token(data=credentials)
        tokens_content = urllib.parse.parse_qs(tokens.content)

        # Parse Ouath Request token and Secret
        oauth_token = tokens_content[b'oauth_token'][0].decode()
        oauth_tokensecret = tokens_content[b'oauth_token_secret'][0].decode()

        # Create a session that will be used for every following request
        session = OAuth1Session(
                clientKey,
                clientSecret,
                oauth_token,
                oauth_tokensecret
        )
        self.session = session

    def get(self, endpoint, urlParams=[], **kwargs):
        for key in urlParams:
            urlParam = str(urlParams[key])
            endpoint = endpoint.replace('{{{}}}'.format(key), urlParam)
        request_url = "%s%s" % (self.baseUrl, endpoint)

        response = self.session.get(
                request_url,
                header_auth=True,
                headers={"Accept": "application/json"},
                **kwargs
        )

        if response.status_code < 300:
            return response

        logger.debug(f"Error: {response.status_code}")
        return None
