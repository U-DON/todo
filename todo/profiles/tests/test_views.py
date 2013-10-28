from django.contrib.auth import get_user_model
from django.test import TestCase

class RegistrationViewTest(TestCase):
    def test_register_with_missing_email(self):
        """Check that registering with no email results in an error."""
        form_data = {'name': 'test', 'password': 'test'}
        response = self.client.post('/register/', form_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")

    def test_register_with_missing_name(self):
        """Check that registering with no name results in an error."""
        form_data = {'email': 'test@test.com', 'password': 'test'}
        response = self.client.post('/register/', form_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")

    def test_register_with_missing_password(self):
        """Check that registering with no password results in an error."""
        form_data = {'email': 'test@test.com', 'name': 'test'}
        response = self.client.post('/register/', form_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")

    def test_register_with_valid_email(self):
        """Check that registering with a valid email creates a new user."""
        form_data = {'email': 'test@test.com', 'name': 'test', 'password': 'test'}
        response = self.client.post('/register/', form_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(get_user_model().objects.count(), 1)
        user = get_user_model().objects.all()[0]
        self.assertEqual(user.name, 'test')
        self.assertEqual(user.email, 'test@test.com')

    def test_register_with_invalid_email(self):
        """Check that registering with an invalid email returns to registration with an error."""
        form_data = {'email': 'test', 'name': 'test', 'password': 'test'}
        response = self.client.post('/register/', form_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter a valid email address.")
        self.assertEqual(get_user_model().objects.count(), 0)

    def test_register_with_existing_email(self):
        """Check that registering with an existing email returns to registration with an error."""
        form_data = {'email': 'test@test.com', 'name': 'test', 'password': 'test'}
        get_user_model().objects.create(**form_data)
        response = self.client.post('/register/', form_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(get_user_model().objects.count(), 1)
