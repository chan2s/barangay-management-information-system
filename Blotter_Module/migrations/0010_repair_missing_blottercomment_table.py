from django.db import migrations


def create_blotter_comment_table_if_missing(apps, schema_editor):
    BlotterComment = apps.get_model('Blotter_Module', 'BlotterComment')
    existing_tables = {
        table.lower()
        for table in schema_editor.connection.introspection.table_names()
    }
    if BlotterComment._meta.db_table.lower() not in existing_tables:
        schema_editor.create_model(BlotterComment)


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('Blotter_Module', '0009_blotter_structured_complainant_address'),
    ]

    operations = [
        migrations.RunPython(create_blotter_comment_table_if_missing, migrations.RunPython.noop),
    ]
