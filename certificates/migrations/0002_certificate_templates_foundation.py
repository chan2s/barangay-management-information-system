from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('certificates', '0001_initial'),
        ('staff_module', '0006_systemsetting_activitylog'),
    ]

    operations = [
        migrations.CreateModel(
            name='CertificateTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('template_name', models.CharField(max_length=200)),
                ('template_type', models.CharField(max_length=50, db_index=True)),
                ('header_html', models.TextField(blank=True, default='')),
                ('body_html', models.TextField(blank=True, default='')),
                ('footer_html', models.TextField(blank=True, default='')),
                ('logo', models.ImageField(blank=True, null=True, upload_to='certificate_assets/%Y/%m/logos/')),
                ('seal', models.ImageField(blank=True, null=True, upload_to='certificate_assets/%Y/%m/seals/')),
                ('signature', models.ImageField(blank=True, null=True, upload_to='certificate_assets/%Y/%m/signatures/')),
                ('is_active', models.BooleanField(default=True, db_index=True)),
                ('is_deleted', models.BooleanField(default=False, db_index=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, null=True, related_name='created_certificate_templates', to='auth.user')),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, null=True, related_name='updated_certificate_templates', to='auth.user')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CertificateTemplatePermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(blank=True, choices=[('admin', 'Admin'), ('staff', 'Staff'), ('kapitan', 'Kapitan')], max_length=20)),
                ('staff_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='certificate_template_permissions', to='auth.user')),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='permissions', to='certificates.certificateTemplate')),
            ],
        ),
        migrations.CreateModel(
            name='CertificateTemplateVersion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('version_number', models.PositiveIntegerField(db_index=True)),
                ('change_notes', models.CharField(max_length=500, blank=True, default='')),
                ('snapshot_header_html', models.TextField(blank=True, default='')),
                ('snapshot_body_html', models.TextField(blank=True, default='')),
                ('snapshot_footer_html', models.TextField(blank=True, default='')),
                ('snapshot_logo', models.ImageField(blank=True, null=True, upload_to='certificate_assets/%Y/%m/version_logos/')),
                ('snapshot_seal', models.ImageField(blank=True, null=True, upload_to='certificate_assets/%Y/%m/version_seals/')),
                ('snapshot_signature', models.ImageField(blank=True, null=True, upload_to='certificate_assets/%Y/%m/version_signatures/')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, null=True, related_name='certificate_template_versions', to='auth.user')),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='certificates.certificateTemplate')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]

