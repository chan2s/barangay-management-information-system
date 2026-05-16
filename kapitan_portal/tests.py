from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Resident, ResidentExportRequest
from staff_module.models import Staff


@override_settings(ALLOWED_HOSTS=['testserver'])
class KapitanResidentExportBoundaryTests(TestCase):
    def setUp(self):
        self.kapitan_user = User.objects.create_user('kapitan', password='pass12345')
        self.admin_user = User.objects.create_user('admin', password='pass12345')
        Staff.objects.create(user=self.kapitan_user, role='kapitan', position='Punong Barangay')
        Staff.objects.create(user=self.admin_user, role='admin', position='Administrator')
        self.resident = Resident.objects.create(
            full_name='Maria Cruz',
            birthdate=date(1950, 1, 1),
            sex='female',
            civil_status='single',
            address='Poblacion, Santa Catalina, Negros Oriental',
            resident_id='RES-001',
            purok='purok_1',
            household_number='HH-001',
            voter_status='registered',
            privacy_consent=True,
        )

    def test_kapitan_resident_page_does_not_show_resident_records(self):
        self.client.force_login(self.kapitan_user)

        response = self.client.get(reverse('kapitan_portal:resident_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Resident Export Requests')
        self.assertNotContains(response, self.resident.full_name)
        self.assertNotContains(response, self.resident.resident_id)

    def test_kapitan_export_request_uses_allowed_filters_only(self):
        self.client.force_login(self.kapitan_user)

        response = self.client.post(
            reverse('kapitan_portal:resident_export_request'),
            {
                'search': 'Maria Cruz',
                'purok': 'purok_1',
                'age_group': 'senior',
                'sex': 'female',
                'reason': 'Senior assistance planning',
            },
        )

        self.assertRedirects(response, reverse('kapitan_portal:resident_list'))
        export_request = ResidentExportRequest.objects.get()
        self.assertEqual(export_request.category, 'filtered')
        self.assertEqual(
            export_request.filters,
            {'purok': 'purok_1', 'age_group': 'senior', 'sex': 'female'},
        )
        self.assertNotIn('search', export_request.filters)

    def test_kapitan_cannot_open_admin_resident_data_page(self):
        self.client.force_login(self.kapitan_user)

        response = self.client.get(reverse('admin_panel:resident_list'))

        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(response.url, reverse('admin_panel:resident_list'))

    def test_admin_approval_is_separate_from_csv_download(self):
        export_request = ResidentExportRequest.objects.create(
            requested_by=self.kapitan_user,
            category='filtered',
            filters={'purok': 'purok_1', 'age_group': 'senior', 'sex': 'female'},
            reason='Senior assistance planning',
        )
        self.client.force_login(self.admin_user)

        review_response = self.client.post(
            reverse('admin_panel:resident_export_review', args=[export_request.id]),
            {'action': 'approve'},
        )

        self.assertRedirects(review_response, reverse('admin_panel:resident_list'))
        export_request.refresh_from_db()
        self.assertEqual(export_request.status, 'approved')
        self.assertEqual(export_request.approved_by, self.admin_user)

        download_response = self.client.get(
            reverse('admin_panel:resident_export_download', args=[export_request.id])
        )

        self.assertEqual(download_response.status_code, 200)
        self.assertEqual(download_response['Content-Type'], 'text/csv')
        self.assertIn(b'Maria Cruz', download_response.content)
