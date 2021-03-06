from django.contrib.auth.models import User
from django.core.validators import email_re

class EmailBackend():
    def authenticate(self, email=None, password=None):
        
        if email_re.search(email):
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return None
        
        if user.check_password(password):
            return user
        
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None