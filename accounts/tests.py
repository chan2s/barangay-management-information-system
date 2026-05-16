from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from staff_module.models import Staff


@override_settings(ALLOWED_HOSTS=['testserver'])
class AuthenticatedEntryRedirectTests(TestCase):
    def assertRedirectsToName(self, response, url_name):
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse(url_name))

    def test_authenticated_admin_is_redirected_away_from_login_and_home(self):
        user = User.objects.create_user('admin-user', password='pass12345')
        Staff.objects.create(user=user, role='admin')
        self.client.force_login(user)

        self.assertRedirectsToName(self.client.get(reverse('login')), 'admin_panel:dashboard')
        self.assertRedirectsToName(self.client.get(reverse('home')), 'admin_panel:dashboard')

    def test_authenticated_staff_is_redirected_away_from_login_and_home(self):
        user = User.objects.create_user('staff-user', password='pass12345')
        Staff.objects.create(user=user, role='staff')
        self.client.force_login(user)

        self.assertRedirectsToName(self.client.get(reverse('login')), 'staff_module:staff_dashboard')
        self.assertRedirectsToName(self.client.get(reverse('home')), 'staff_module:staff_dashboard')

    def test_authenticated_kapitan_is_redirected_away_from_login_and_home(self):
        user = User.objects.create_user('kapitan-user', password='pass12345')
        Staff.objects.create(user=user, role='kapitan')
        self.client.force_login(user)

        self.assertRedirectsToName(self.client.get(reverse('login')), 'kapitan_portal:dashboard')
        self.assertRedirectsToName(self.client.get(reverse('home')), 'kapitan_portal:dashboard')

    def test_logged_out_user_can_visit_login_and_home(self):
        self.assertEqual(self.client.get(reverse('login')).status_code, 200)
        self.assertEqual(self.client.get(reverse('home')).status_code, 200)
