from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('acervo', '0002_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='obra',
            old_name='editora_id',
            new_name='editora',
        ),
    ]
