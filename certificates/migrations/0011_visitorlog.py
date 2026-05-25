from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('certificates', '0010_certificatetemplate_document_html_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='VisitorLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField(blank=True, db_index=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('visited_path', models.CharField(max_length=2048)),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                'verbose_name': 'Visitor Log',
                'verbose_name_plural': 'Visitor Logs',
                'ordering': ['-timestamp'],
                'indexes': [models.Index(fields=['timestamp', 'ip_address'], name='certificate_timesta_21950c_idx')],
            },
        ),
    ]
