from django.conf import settings
settings.configure()

from drf_social_oauth2.authentication import SocialAuthentication



class AuthenticateTextCase:
    @staticmethod
    def authorization_header_response():
        return 'nothing'

    def test_authenticate_no_auth_header_fail(self, monkeypatch):
        def mock_get(*args, **kwargs):
            return 'nothing'

        authenticated = SocialAuthentication()
        # apply the monkeypatch for requests.get to mock_get
        monkeypatch.setattr(
            SocialAuthentication,
            'get_authorization_header',
            mock_get
        )

        print(authenticated.authenticate())
