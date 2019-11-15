#from requests_oauthlib import OAuth1Session
import urllib
import json
import requests

from rauth import *
from base64 import b64encode

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
        :param password: FellowshipOne password
        :type password: string"""

        # CT fellowshipone base URL
        self.baseUrl = "https://christny.staging.fellowshiponeapi.com/"

        # Hash credentials
        credential_string = "{} {}".format(username, password)
        credentials = b64encode(bytes(credential_string, "utf-8"))
        credentials = urllib.parse.quote_plus( credentials )

        # Setup OAuth1 Service to retrive Request Tokens
        service = OAuth1Service (
           consumer_key = client_key,
           consumer_secret = client_secret,
           request_token_url = "%s/v1/PortalUser/AccessToken" % self.baseUrl
        )
        
        # Fetch tokens from fellowship one
        tokens = service.get_raw_request_token(data = credentials)
        tokens_content = urllib.parse.parse_qs(tokens.content)

        # Parse Ouath Request token and Secret
        oauth_token = tokens_content[b'oauth_token'][0].decode()
        oauth_tokensecret = tokens_content[b'oauth_token_secret'][0].decode()
        
        # Create a session that will be used for every following request
        session = OAuth1Session (clientKey, clientSecret, oauth_token, oauth_tokensecret)
        self.session = session
