# Generated by Django 5.0.2 on 2024-08-05 09:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fileAnalyzer', '0005_review_reviewmodes'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='bleuScore',
            field=models.FloatField(default=-1),
        ),
        migrations.AddField(
            model_name='review',
            name='codeBleuScore',
            field=models.FloatField(default=-1),
        ),
        migrations.AddField(
            model_name='review',
            name='crystalBleuScore',
            field=models.FloatField(default=-1),
        ),
    ]
