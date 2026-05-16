from django.core.management.base import BaseCommand
from django.utils import timezone
from staff_module.models import Appointment
from Blotter_Module.models import Blotter, Schedule

class Command(BaseCommand):
    help = 'Sync existing scheduled blotters to appointments'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting sync of scheduled blotters...'))
        
        # Get all schedules that don't have corresponding appointments
        schedules = Schedule.objects.filter(
            hearing_date__gte=timezone.now()
        )
        
        count = 0
        for schedule in schedules:
            blotter = schedule.blotter
            
            # Check if appointment already exists for this blotter hearing
            existing_appt = Appointment.objects.filter(
                blotter=blotter,
                appointment_type='blotter_hearing'
            ).first()
            
            if not existing_appt:
                # Create appointment
                appointment = Appointment.objects.create(
                    appointment_type='blotter_hearing',
                    blotter=blotter,
                    resident_name=blotter.complainant_name,
                    resident_address=blotter.complainant_address,
                    resident_contact=blotter.complainant_phone or '',
                    resident_email=blotter.complainant_email or '',
                    purpose=f"Blotter Hearing: {blotter.get_incident_type_display()} - {blotter.blotter_number}",
                    appointment_date=schedule.hearing_date,
                    duration_minutes=30,
                    priority='important',
                    hearing_type=schedule.hearing_type,
                    location=schedule.location,
                    status='approved',
                    created_by=schedule.created_by,
                    approved_by=schedule.created_by,
                    approved_at=timezone.now(),
                    notes=f"Auto-generated from blotter schedule. Original notes: {schedule.notes or ''}"
                )
                count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created appointment for blotter {blotter.blotter_number} - Ref: {appointment.reference_number}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠ Appointment already exists for blotter {blotter.blotter_number}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully created {count} new appointments from scheduled blotters'))