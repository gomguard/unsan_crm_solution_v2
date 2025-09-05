# Generated manually for search performance optimization

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0002_remove_servicerequest_customer_email_and_more'),
    ]

    operations = [
        # Add database indexes for better search performance
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS services_servicerequest_customer_phone_idx ON services_servicerequest(customer_phone);",
            reverse_sql="DROP INDEX IF EXISTS services_servicerequest_customer_phone_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS services_servicerequest_customer_name_idx ON services_servicerequest(customer_name);",
            reverse_sql="DROP INDEX IF EXISTS services_servicerequest_customer_name_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS services_servicerequest_vehicle_number_idx ON services_servicerequest(vehicle_number);",
            reverse_sql="DROP INDEX IF EXISTS services_servicerequest_vehicle_number_idx;"
        ),
        # Composite index for frequent queries
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS services_servicerequest_phone_vehicle_idx ON services_servicerequest(customer_phone, vehicle_number);",
            reverse_sql="DROP INDEX IF EXISTS services_servicerequest_phone_vehicle_idx;"
        ),
    ]