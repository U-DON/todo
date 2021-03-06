from django.contrib.auth import get_user_model
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase

class RegistrationViewTest(TestCase):
    def test_register_with_valid_email(self):
        """Checks that registering with a valid email creates a new user."""
        form_data = {'email': 'test@test.com', 'name': 'test', 'password': 'test', 'timezone': 'UTC'}
        response = self.client.post(reverse('profiles:register'), form_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(get_user_model().objects.count(), 1)
        user = get_user_model().objects.all()[0]
        self.assertEqual(user.name, 'test')
        self.assertEqual(user.email, 'test@test.com')

    def test_register_with_missing_email(self):
        """Checks that registering with no email raises an error."""
        form_data = {'email': '', 'name': 'test', 'password': 'test', 'timezone': 'UTC'}
        response = self.client.post(reverse('profiles:register'), form_data)
        self.assertFormError(response, 'form', 'email', "This field is required.")

    def test_register_with_missing_name(self):
        """Checks that registering with no name raises an error."""
        form_data = {'email': 'test@test.com', 'name': '', 'password': 'test', 'timezone': 'UTC'}
        response = self.client.post(reverse('profiles:register'), form_data)
        self.assertFormError(response, 'form', 'name', "This field is required.")

    def test_register_with_missing_password(self):
        """Checks that registering with no password raises an error."""
        form_data = {'email': 'test@test.com', 'name': 'test', 'password': '', 'timezone': 'UTC'}
        response = self.client.post(reverse('profiles:register'), form_data)
        self.assertFormError(response, 'form', 'password', "This field is required.")

    def test_register_with_missing_timezone(self):
        """Checks that registering with no timezone raises an error."""
        form_data = {'email': 'test@test.com', 'name': 'test', 'password': 'test', 'timezone': ''}
        response = self.client.post(reverse('profiles:register'), form_data)
        self.assertFormError(response, 'form', 'timezone', "This field is required.")

    def test_register_with_invalid_email(self):
        """Checks that registering with an invalid email returns to registration with an error."""
        form_data = {'email': 'test', 'name': 'test', 'password': 'test', 'timezone': 'UTC'}
        response = self.client.post(reverse('profiles:register'), form_data)
        self.assertFormError(response, 'form', 'email', "Enter a valid email address.")
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_register_with_existing_email(self):
        """Checks that registering with an existing email returns to registration with an error."""
        form_data = {'email': 'test@test.com', 'name': 'test', 'password': 'test'}
        get_user_model().objects.create_user(**form_data)
        form_data['timezone'] = 'UTC'
        response = self.client.post(reverse('profiles:register'), form_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_register_with_invalid_timezone(self):
        """Checks that registering with an invalid timezone raises an error."""
        form_data = {'email': 'test@test.com', 'name': 'test', 'password': 'test', 'timezone': 'UUTTCC'}
        response = self.client.post(reverse('profiles:register'), form_data)
        self.assertFormError(response, 'form', 'timezone', "Select a valid choice. UUTTCC is not one of the available choices.")

class LoginViewTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(email='test@test.com', name='test', password='test')

    def test_login_with_valid_credentials(self):
        """Checks that logging in with an existing account is successful."""
        form_data = {'email': self.user.email, 'password': 'test', 'timezone': 'UTC'}
        response = self.client.post(reverse('profiles:login'), form_data)
        self.assertEqual(response.status_code, 200)

    def test_login_with_blank_email(self):
        """Checks that logging in with a blank email raises an error."""
        form_data = {'email': '', 'password': 'test', 'timezone': 'UTC'}
        response = self.client.post(reverse('profiles:login'), form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'username', "This field is required.")

    def test_login_with_nonexistent_account(self):
        """Checks that logging in with a nonexistent account raises an error."""
        form_data = {'email': 'john.doe@test.com', 'password': 'test', 'timezone': 'UTC'}
        response = self.client.post(reverse('profiles:login'), form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'username', [])

    def test_login_with_blank_password(self):
        """Checks that logging in with a blank password raises an error."""
        form_data = {'email': self.user.email, 'password': ''}
        response = self.client.post(reverse('profiles:login'), form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'password', "This field is required.")

    def test_login_with_invalid_password(self):
        """Checks that logging in with an invalid password raises an error."""
        form_data = {'email': self.user.email, 'password': '123'}
        response = self.client.post(reverse('profiles:login'), form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'password', [])

class PasswordResetViewTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(email='test@test.com', name='test', password='test')

    def test_password_reset_sends_email(self):
        """Checks that requesting a password reset sends the email."""
        form_data = {'email': self.user.email}
        response = self.client.post(reverse('profiles:password_reset'), form_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        # self.assertEqual(mail.outbox[0].subject, "Password reset")
        # self.assertEqual(mail.outbox[0].body, "")
