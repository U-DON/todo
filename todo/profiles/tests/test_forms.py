from django.test import TestCase

from ..forms import RegistrationForm

class RegistrationFormTest(TestCase):
    def test_register_with_valid_form(self):
        """Checks that a form with valid inputs is valid."""
        form_data = {'email': 'test@test.com', 'name': 'test', 'password': 'test', 'timezone': 'UTC'}
        form = RegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_register_with_invalid_email(self):
        """Checks that a form with an invalid email is invalid."""
        form_data = {'email': 'test', 'name': 'test', 'password': 'test', 'timezone': 'UTC'}
        form = RegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())

        form_data['email'] = 'test@'
        form = RegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())

        form_data['email'] = 'test@test'
        form = RegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())

        form_data['email'] = 'test.com'
        form = RegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_register_with_blank_name(self):
        """Checks that a form with a blank name is invalid."""
        form_data = {'email': 'test@test.com', 'name': '', 'password': 'test', 'timezone': 'UTC'}
        form = RegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_register_with_blank_password(self):
        """Checks that a form with a blank password is invalid."""
        form_data = {'email': 'test@test.com', 'name': 'test', 'password': '', 'timezone': 'UTC'}
        form = RegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_register_with_blank_timezone(self):
        """Checks that a form with a blank timezone is invalid."""
        form_data = {'email': 'test@test.com', 'name': 'test', 'password': 'test', 'timezone': ''}
        form = RegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_register_with_invalid_timezone(self):
        """Checks that a form with an invalid timezone is invalid."""
        form_data = {'email': 'test@test.com', 'name': 'test', 'password': 'test', 'timezone': 'UUTTCC'}
        form = RegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
