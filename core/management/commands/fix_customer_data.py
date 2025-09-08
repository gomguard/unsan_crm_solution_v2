from django.core.management.base import BaseCommand
from customers.models import Customer
from services.models import ServiceRequest
from django.db.models import Q


class Command(BaseCommand):
    help = 'Fix customer data issues - grades and service counts'

    def handle(self, *args, **options):
        # Fix 'NaT' customer grades
        nat_customers = Customer.objects.filter(customer_grade='NaT')
        nat_count = nat_customers.count()
        self.stdout.write(f'Found {nat_count} customers with NaT grades')
        nat_customers.update(customer_grade='')
        self.stdout.write(f'Fixed {nat_count} customer grades')

        # Update service counts for all customers
        customers = Customer.objects.all()
        count = 0
        for customer in customers:
            try:
                service_count = ServiceRequest.objects.filter(
                    Q(customer=customer) | 
                    Q(temp_customer_name=customer.name, temp_customer_phone=customer._get_raw_phone())
                ).count()
                
                if customer.total_service_count != service_count:
                    customer.total_service_count = service_count
                    customer.save()
                    count += 1
                    if count % 100 == 0:
                        self.stdout.write(f'Updated {count} customers...')
            except Exception as e:
                self.stdout.write(f'Error updating customer {customer.id}: {e}')

        self.stdout.write(f'Updated service counts for {count} customers')
        
        # Show some sample results
        samples = Customer.objects.all()[:5]
        for customer in samples:
            self.stdout.write(f'Customer {customer.id}: Grade={customer.customer_grade}, Services={customer.total_service_count}')