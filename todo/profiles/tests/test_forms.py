from django.test import TestCase

from ..forms import RegistrationForm

class RegistrationFormTest(TestCase):
    def test_register_with_valid_email(self):
        """Check that a form with a valid email is valid."""
        form_data = {'email': 'test@test.com', 'name': 'test', 'password': 'test'}
        form = RegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_register_with_invalid_email(self):
        """Check that a form with an invalid email is invalid."""
        form_data = {'email': 'test', 'name': 'test', 'password': 'test'}
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
