from django.db import migrations, models


def combine_existing_template_sections(apps, schema_editor):
    CertificateTemplate = apps.get_model('certificates', 'CertificateTemplate')
    for template in CertificateTemplate.objects.all():
        if template.document_html:
            continue
        parts = [template.header_html or '', template.body_html or '', template.footer_html or '']
        template.document_html = '\n'.join(part for part in parts if part.strip())
        template.save(update_fields=['document_html'])


class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0009_alter_certificatetemplate_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='certificatetemplate',
            name='document_html',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='certificatetemplateversion',
            name='snapshot_document_html',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.RunPython(combine_existing_template_sections, migrations.RunPython.noop),
    ]
