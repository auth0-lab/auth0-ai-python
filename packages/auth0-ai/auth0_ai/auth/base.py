from __future__ import annotations
import os
from auth0.authentication.base import AuthenticationBase

class BaseAuth(AuthenticationBase):
    """Base authentication class with core properties and validations"""
    # Define required config fields and their environment variable names
    REQUIRED_CONFIGS = {
        'domain': 'AUTH0_DOMAIN',
        'client_id': 'AUTH0_CLIENT_ID',
        'client_secret': 'AUTH0_CLIENT_SECRET',
        'redirect_uri': 'AUTH0_REDIRECT_URI',
        'secret_key': 'AUTH0_SECRET_KEY'
    }
    
    def __init__(
            self,
            domain: str | None = None,
            client_id: str | None = None,
            client_secret: str | None = None,
            redirect_uri: str | None = None,
            secret_key: str | None = None,
            *args, **kwargs):
        
        # Initialize all config properties
        for field, env_var in self.REQUIRED_CONFIGS.items():
            value = locals().get(field) or os.environ.get(env_var)
            setattr(self, f'_{field}', None)  # Initialize private attribute
            setattr(self.__class__, field, property(  # Create property
                fget=lambda self, f=field: getattr(self, f'_{f}'),
                fset=lambda self, value, f=field: self._validate_and_set(f, value)
            ))
            setattr(self, field, value)  # Set the value using property setter

        super().__init__(
            domain=self.domain,
            client_id=self.client_id,
            client_secret=self.client_secret,
            *args, **kwargs
        )

    def _validate_and_set(self, field: str, value: str | None) -> None:
        """Validate and set a configuration value"""
        if not value:
            raise ValueError(
                f"{field} cannot be empty. You can also set {self.REQUIRED_CONFIGS[field]} value in .env file")
        setattr(self, f'_{field}', value)