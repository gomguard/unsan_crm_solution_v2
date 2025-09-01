from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from customers.models import Customer, Tag, CustomerTag
import random
from datetime import date, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = '간단한 샘플 데이터 생성'

    def handle(self, *args, **options):
        self.stdout.write('샘플 데이터 생성 시작...')
        
        # 관리자 계정 생성
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@unsan.com',
                password='admin123'
            )
            self.stdout.write('관리자 계정 생성: admin/admin123')
        
        # 기본 태그 생성
        tags_data = [
            ('우수고객', '#10B981'),
            ('단골고객', '#3B82F6'),
            ('신규고객', '#8B5CF6'),
            ('VIP고객', '#F59E0B'),
            ('주의고객', '#EF4444'),
        ]
        
        for name, color in tags_data:
            Tag.objects.get_or_create(name=name, defaults={'color': color})
        
        # 샘플 고객 1000명 생성
        customers = []
        phone_numbers = set()
        
        surnames = ['김', '이', '박', '최', '정', '강', '조', '윤', '장', '임']
        first_names = ['민수', '영희', '철수', '순이', '진수', '미영', '동현', '수진', '현우', '지영']
        
        for i in range(1000):
            # 고유한 전화번호 생성
            while True:
                phone = f"010{random.randint(1000, 9999)}{random.randint(1000, 9999)}"
                if phone not in phone_numbers:
                    phone_numbers.add(phone)
                    break
            
            # 고객 상태 (80% 정식, 20% 임시)
            customer_status = 'registered' if random.random() < 0.8 else 'temporary'
            customer_type = 'individual' if random.random() < 0.9 else 'corporate'
            
            # 이름 생성
            if customer_status == 'temporary':
                name = None
            else:
                name = random.choice(surnames) + random.choice(first_names)
            
            # 멤버십 (60% 비회원)
            membership_status = 'none'
            if random.random() > 0.6:
                membership_status = random.choice(['basic', 'premium', 'vip'])
            
            customer = Customer(
                customer_status=customer_status,
                customer_type=customer_type,
                name=name,
                phone=phone,
                email=f"user{i}@example.com" if random.random() < 0.5 else '',
                membership_status=membership_status,
                membership_points=random.randint(0, 10000) if membership_status != 'none' else 0,
                marketing_consent=random.choice([True, False]),
                total_service_count=random.randint(0, 20),
                total_service_amount=random.randint(0, 1000000),
                created_at=timezone.now() - timedelta(days=random.randint(1, 730))
            )
            customers.append(customer)
        
        # 배치 생성
        Customer.objects.bulk_create(customers, batch_size=100)
        self.stdout.write('1000명 고객 생성 완료!')
        
        self.stdout.write(
            self.style.SUCCESS('샘플 데이터 생성 완료!')
        )