from django.conf import settings
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, email, name, password):
        """Creates and saves a user with a given email, name, and password."""
        if not email:
            raise ValueError("Email is required.")

        if not name:
            raise ValueError("Name is required.")

        if not password:
            raise ValueError("Password is required.")

        user = self.model(
            email=self.normalize_email(email),
            name=name
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password):
        """Creates and saves a superuser with a given email, name, and password."""
        user = self.create_user(
            email=self.normalize_email(email),
            name=name,
            password=password
        )

        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user

class User(AbstractBaseUser):
    email = models.EmailField(
        max_length=255,
        unique=True,
        db_index=True
    )
    name = models.CharField(max_length=255)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    def get_full_name(self):
        return self.name

    def get_short_name(self):
        return self.name.split()[0]

    def __unicode__(self):
        return self.email

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL)
    timezone = models.CharField(max_length=50)

    def __unicode__(self):
        return self.user.email
