from datetime import date

from django.core.management.base import BaseCommand

from accounts.models import Resident
from accounts.services import fingerprint_sensitive_value


class Command(BaseCommand):
    help = 'Seed 100 realistic Barangay Poblacion resident records.'

    first_names_male = [
        'Jose', 'Juan', 'Mark', 'Christian', 'Paul', 'Ramon', 'Carlo', 'Miguel', 'Andres', 'Jasper',
        'Rogelio', 'Dante', 'Nestor', 'Antonio', 'Gabriel', 'Joshua', 'Ryan', 'Noel', 'Edwin', 'Luis',
    ]
    first_names_female = [
        'Maria', 'Ana', 'Cristina', 'Angelica', 'Jessa', 'Marites', 'Lorna', 'Leah', 'Mary Ann', 'Rica',
        'Catherine', 'Rosemarie', 'Daisy', 'Joanna', 'Michelle', 'Aileen', 'Grace', 'Sofia', 'Erika', 'Camille',
    ]
    surnames = [
        'Dela Cruz', 'Garcia', 'Reyes', 'Santos', 'Ramos', 'Mendoza', 'Flores', 'Gonzales', 'Bautista', 'Villanueva',
        'Fernandez', 'Torres', 'Aquino', 'Castillo', 'Rivera', 'Domingo', 'Navarro', 'Salazar', 'Mercado', 'Valdez',
    ]
    middle_names = ['Santos', 'Reyes', 'Cruz', 'Flores', 'Ramos', 'Garcia', 'Torres', 'Bautista']
    occupations = [
        'Student', 'Farmer', 'Teacher', 'Vendor', 'Driver', 'Fisherfolk', 'Carpenter', 'Barangay Worker',
        'Store Owner', 'Construction Worker', 'Nurse', 'Office Staff', 'Retired', 'Housekeeper', 'Mechanic',
    ]
    streets = [
        'Poblacion Proper', 'Municipal Hall Area', 'Public Market Area', 'Church Area',
        'National Road', 'School Area', 'Barangay Hall Area',
    ]

    def handle(self, *args, **options):
        created = 0
        current_year = date.today().year

        for i in range(1, 101):
            household = f'HH-{((i - 1) // 4) + 1:03d}'
            sex = 'male' if i % 2 else 'female'
            first_pool = self.first_names_male if sex == 'male' else self.first_names_female
            first_name = first_pool[i % len(first_pool)]
            surname = self.surnames[(i + ((i - 1) // 4)) % len(self.surnames)]
            middle = self.middle_names[i % len(self.middle_names)]
            age = self._age_for_index(i)
            birth_year = current_year - age
            birthdate = date(birth_year, ((i - 1) % 12) + 1, ((i - 1) % 27) + 1)
            purok_number = ((i - 1) % 7) + 1
            street = self.streets[(i - 1) % len(self.streets)]
            resident_id = f'BIMS-RES-{i:04d}'
            national_id = f'PH{birth_year}{i:08d}'

            _, was_created = Resident.objects.update_or_create(
                resident_id=resident_id,
                defaults={
                    'full_name': f'{first_name} {middle} {surname}',
                    'middle_name': middle,
                    'suffix': 'Jr.' if i in (17, 43, 79) else '',
                    'birthdate': birthdate,
                    'sex': sex,
                    'civil_status': 'single' if age < 25 else ('married' if i % 5 else 'widowed'),
                    'street_name': street,
                    'purok': f'purok_{purok_number}',
                    'address': f'{street}, Purok {purok_number}, Poblacion, Santa Catalina, Negros Oriental',
                    'barangay': 'Poblacion',
                    'municipality': 'Santa Catalina',
                    'province': 'Negros Oriental',
                    'contact_number': f'09{170000000 + i:09d}',
                    'email': f'resident{i:03d}@example.com',
                    'national_id_hash': fingerprint_sensitive_value(national_id),
                    'national_id_last4': national_id[-4:],
                    'household_number': household,
                    'occupation': 'Student' if age < 22 else ('Retired' if age >= 60 else self.occupations[i % len(self.occupations)]),
                    'is_solo_parent': i % 19 == 0,
                    'is_indigent': i % 6 == 0,
                    'voter_status': 'registered' if age >= 18 and i % 4 else ('not_registered' if age >= 18 else 'unknown'),
                    'privacy_consent': True,
                    'is_deleted': False,
                },
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f'Seeded residents. New records created: {created}; total sample target: 100.'))

    def _age_for_index(self, index):
        if index <= 18:
            return 6 + (index % 12)
        if index <= 35:
            return 18 + (index % 12)
        if index <= 78:
            return 30 + (index % 25)
        return 60 + (index % 25)
