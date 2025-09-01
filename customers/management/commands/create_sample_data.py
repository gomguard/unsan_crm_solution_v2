from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from customers.models import (
    Customer, Tag, CustomerTag, Vehicle, CustomerVehicle,
    CustomerCommunication, HappyCall, MarketingCampaign,
    CustomerCampaignHistory, CustomerPointHistory
)
import random
from datetime import date, datetime, timedelta
from faker import Faker

User = get_user_model()
fake = Faker('ko_KR')


class Command(BaseCommand):
    help = '운산자동차 CRM 샘플 데이터 생성'

    def add_arguments(self, parser):
        parser.add_argument(
            '--customers',
            type=int,
            default=1000,
            help='생성할 고객 수 (기본: 1000)'
        )

    def handle(self, *args, **options):
        customer_count = options['customers']
        
        self.stdout.write(f'운산자동차 CRM 샘플 데이터 생성 시작 ({customer_count}명)')
        
        # 1. 관리자 계정 생성 (없는 경우)
        self.create_admin_user()
        
        # 2. 기본 태그 생성
        self.create_tags()
        
        # 3. 고객 데이터 생성
        self.create_customers(customer_count)
        
        # 4. 차량 데이터 생성
        self.create_vehicles()
        
        # 5. 고객-차량 관계 생성
        self.create_customer_vehicles()
        
        # 6. 소통 이력 생성
        self.create_communications()
        
        # 7. 해피콜 데이터 생성
        self.create_happy_calls()
        
        # 8. 마케팅 캠페인 생성
        self.create_marketing_campaigns()
        
        self.stdout.write(
            self.style.SUCCESS(f'샘플 데이터 생성 완료!')
        )

    def create_admin_user(self):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@unsan.com',
                password='admin123'
            )
            self.stdout.write('관리자 계정 생성: admin/admin123')

    def create_tags(self):
        tags_data = [
            ('우수고객', '#10B981'),      # 초록
            ('단골고객', '#3B82F6'),      # 파랑
            ('신규고객', '#8B5CF6'),      # 보라
            ('VIP고객', '#F59E0B'),       # 주황
            ('주의고객', '#EF4444'),      # 빨강
            ('멤버십고객', '#06B6D4'),    # 청록
            ('법인고객', '#6B7280'),      # 회색
            ('이탈위험', '#F97316'),      # 주황빨강
            ('휴면고객', '#64748B'),      # 슬레이트
            ('추천고객', '#EC4899'),      # 핑크
        ]
        
        for name, color in tags_data:
            Tag.objects.get_or_create(name=name, defaults={'color': color})
        
        self.stdout.write(f'{len(tags_data)}개 태그 생성 완료')

    def create_customers(self, count):
        customers = []
        phone_numbers = set()
        
        # 한국 성씨와 이름 리스트
        surnames = ['김', '이', '박', '최', '정', '강', '조', '윤', '장', '임', '한', '오', '서', '신', '권', '황', '안', '송', '류', '전']
        first_names = ['민수', '영희', '철수', '순이', '진수', '미영', '동현', '수진', '현우', '지영', '태현', '소영', '준혁', '은주', '성호', '혜진', '우진', '다혜', '상현', '아영']
        
        # 회사명 리스트
        company_types = ['㈜', '(주)', '']
        company_names = ['대한', '한국', '신한', '우리', '하나', '국민', '농협', '신협', '현대', '삼성', 'LG', 'SK', '롯데', '두산', '한화', '포스코', '효성', '금호', '한진', '대우']
        company_suffixes = ['상사', '기업', '산업', '건설', '개발', '무역', '엔지니어링', '시스템', '테크', '솔루션']
        
        acquisition_sources = ['지인소개', '인터넷검색', '광고', '전단지', '지나가다가', '단골소개', '기존고객추천', '직접방문']
        
        for i in range(count):
            # 고유한 전화번호 생성
            while True:
                phone = f"010{random.randint(1000, 9999)}{random.randint(1000, 9999)}"
                if phone not in phone_numbers:
                    phone_numbers.add(phone)
                    break
            
            # 고객 타입 결정 (90% 개인, 10% 법인)
            customer_type = 'individual' if random.random() < 0.9 else 'corporate'
            
            # 고객 상태 (80% 정식고객, 15% 임시고객, 5% 잠재고객)
            status_weights = [('registered', 0.8), ('temporary', 0.15), ('prospect', 0.05)]
            customer_status = random.choices(
                [status for status, weight in status_weights],
                weights=[weight for status, weight in status_weights]
            )[0]
            
            # 이름 생성
            if customer_status == 'temporary':
                name = None  # 임시고객은 이름 없음
            else:
                if customer_type == 'corporate':
                    company_type = random.choice(company_types)
                    company_base = random.choice(company_names)
                    company_suffix = random.choice(company_suffixes)
                    name = f"{company_type}{company_base}{company_suffix}"
                else:
                    name = random.choice(surnames) + random.choice(first_names)
            
            # 멤버십 상태 (60% 비회원, 25% 일반회원, 10% 우수회원, 5% VIP)
            membership_weights = [('none', 0.6), ('basic', 0.25), ('premium', 0.1), ('vip', 0.05)]
            membership_status = random.choices(
                [status for status, weight in membership_weights],
                weights=[weight for status, weight in membership_weights]
            )[0]
            
            # 멤버십 가입일 (회원인 경우만)
            membership_join_date = None
            membership_points = 0
            if membership_status != 'none':
                membership_join_date = fake.date_between(start_date='-2y', end_date='today')
                membership_points = random.randint(0, 50000)
            
            # 주소 생성
            address_main = fake.address() if random.random() < 0.7 else ''
            
            # 법인 정보 (법인 고객인 경우)
            business_number = ''
            company_name = ''
            if customer_type == 'corporate':
                business_number = f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10000, 99999)}"
                company_name = name if name else ''
            
            # 고객 등급 (정식고객만)
            customer_grade = ''
            if customer_status == 'registered':
                grade_weights = [('A', 0.1), ('B', 0.25), ('C', 0.45), ('D', 0.2)]
                customer_grade = random.choices(
                    [grade for grade, weight in grade_weights],
                    weights=[weight for grade, weight in grade_weights]
                )[0]
            
            customer = Customer(
                customer_status=customer_status,
                customer_type=customer_type,
                name=name,
                phone=phone,
                email=fake.email() if random.random() < 0.6 else '',
                address_main=address_main,
                address_detail=fake.building_number() + '호' if address_main and random.random() < 0.5 else '',
                business_number=business_number,
                company_name=company_name,
                membership_status=membership_status,
                membership_join_date=membership_join_date,
                membership_points=membership_points,
                marketing_consent=random.choice([True, False]),
                marketing_consent_date=timezone.make_aware(timezone.make_aware(fake.date_time_between(start_date='-1y', end_date='now')) if random.random() < 0.7 else None,
                preferred_contact_method=random.choice(['sms', 'phone', 'email']),
                do_not_contact=random.choice([True, False]) if random.random() < 0.1 else False,
                acquisition_source=random.choice(acquisition_sources),
                customer_grade=customer_grade,
                first_service_date=fake.date_between(start_date='-2y', end_date='today') if random.random() < 0.8 else None,
                last_service_date=fake.date_between(start_date='-6m', end_date='today') if random.random() < 0.6 else None,
                total_service_count=random.randint(0, 50),
                total_service_amount=random.randint(0, 5000000),
                notes=fake.text(max_nb_chars=200) if random.random() < 0.3 else '',
                created_at=timezone.make_aware(timezone.make_aware(fake.date_time_between(start_date='-2y', end_date='now'))
            )
            customers.append(customer)
        
        # 배치로 생성
        Customer.objects.bulk_create(customers, batch_size=100)
        self.stdout.write(f'{count}명 고객 생성 완료')
        
        # 태그 할당
        self.assign_tags_to_customers()

    def assign_tags_to_customers(self):
        customers = list(Customer.objects.all())
        tags = list(Tag.objects.all())
        admin_user = User.objects.first()
        
        customer_tags = []
        
        for customer in customers:
            # 각 고객에게 0~3개의 태그 랜덤 할당
            num_tags = random.choices([0, 1, 2, 3], weights=[0.3, 0.4, 0.2, 0.1])[0]
            
            if num_tags > 0:
                selected_tags = random.sample(tags, min(num_tags, len(tags)))
                
                for tag in selected_tags:
                    customer_tags.append(CustomerTag(
                        customer=customer,
                        tag=tag,
                        created_by=admin_user,
                        created_at=timezone.make_aware(fake.date_time_between(start_date=customer.created_at, end_date='now')
                    ))
        
        CustomerTag.objects.bulk_create(customer_tags, batch_size=100)
        self.stdout.write(f'고객 태그 {len(customer_tags)}개 할당 완료')

    def create_vehicles(self):
        # 한국 차량 모델명
        car_brands = {
            '현대': ['아반떼', '소나타', '그랜저', '제네시스', '투싼', '싼타페', '팰리세이드', 'i30', '벨로스터'],
            '기아': ['모닝', '레이', '프라이드', 'K3', 'K5', 'K7', 'K9', '스포티지', '쏘렌토', '모하비'],
            '쌍용': ['티볼리', '코란도', '렉스턴', '체어맨'],
            '르노삼성': ['SM3', 'SM5', 'SM7', 'QM3', 'QM5', 'QM6'],
            'GM대우': ['마티즈', '라세티', '아베오', '크루즈', '말리부', '캡티바'],
            '수입차': ['BMW', '벤츠', '아우디', '렉서스', '토요타', '혼다', '폭스바겐', '볼보']
        }
        
        vehicles = []
        vehicle_numbers = set()
        
        # 차량번호 패턴
        regions = ['서울', '부산', '대구', '인천', '광주', '대전', '울산', '경기', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주']
        
        for i in range(1500):  # 고객보다 많은 차량 생성 (중고차 거래 등 고려)
            # 고유한 차량번호 생성
            while True:
                region = random.choice(regions)
                numbers = f"{random.randint(10, 99)}{random.choice(['가', '나', '다', '라', '마', '바', '사', '아', '자'])}{random.randint(1000, 9999)}"
                vehicle_number = f"{region}{numbers}"
                if vehicle_number not in vehicle_numbers:
                    vehicle_numbers.add(vehicle_number)
                    break
            
            # 차량 모델 선택
            brand = random.choice(list(car_brands.keys()))
            model = f"{brand} {random.choice(car_brands[brand])}"
            
            # 연식 (2010~2024)
            year = random.randint(2010, 2024)
            
            vehicles.append(Vehicle(
                vehicle_number=vehicle_number,
                model=model,
                year=year,
                created_at=timezone.make_aware(timezone.make_aware(fake.date_time_between(start_date='-2y', end_date='now'))
            ))
        
        Vehicle.objects.bulk_create(vehicles, batch_size=100)
        self.stdout.write(f'{len(vehicles)}대 차량 생성 완료')

    def create_customer_vehicles(self):
        customers = list(Customer.objects.filter(customer_status='registered'))
        vehicles = list(Vehicle.objects.all())
        
        customer_vehicles = []
        used_vehicles = set()
        
        for customer in customers:
            # 80% 확률로 차량 소유
            if random.random() < 0.8:
                # 사용 가능한 차량 중 선택
                available_vehicles = [v for v in vehicles if v.id not in used_vehicles]
                if available_vehicles:
                    vehicle = random.choice(available_vehicles)
                    used_vehicles.add(vehicle.id)
                    
                    # 소유 시작일
                    start_date = fake.date_between(start_date='-2y', end_date='today')
                    
                    # 90% 확률로 현재도 소유중 (end_date = None)
                    end_date = None
                    if random.random() < 0.1:  # 10% 확률로 이미 판매
                        end_date = fake.date_between(start_date=start_date, end_date='today')
                    
                    customer_vehicles.append(CustomerVehicle(
                        customer=customer,
                        vehicle=vehicle,
                        start_date=start_date,
                        end_date=end_date,
                        created_at=timezone.make_aware(fake.date_time_between(start_date=start_date, end_date='now')
                    ))
        
        CustomerVehicle.objects.bulk_create(customer_vehicles, batch_size=100)
        self.stdout.write(f'고객-차량 관계 {len(customer_vehicles)}건 생성 완료')

    def create_communications(self):
        customers = list(Customer.objects.all()[:500])  # 일부 고객만 선택
        admin_user = User.objects.first()
        
        communications = []
        
        for customer in customers:
            # 고객당 0~10개의 소통 이력 생성
            num_comms = random.choices([0, 1, 2, 3, 4, 5], weights=[0.1, 0.2, 0.3, 0.2, 0.1, 0.1])[0]
            
            for _ in range(num_comms):
                comm_type = random.choice(['consultation', 'marketing', 'complaint', 'inquiry', 'follow_up'])
                method = random.choice(['sms', 'phone', 'email', 'visit'])
                direction = random.choice(['inbound', 'outbound'])
                result = random.choice(['success', 'no_answer', 'refused', 'failed'])
                
                # 제목 생성
                titles = {
                    'consultation': ['정기점검 상담', '수리 문의', '부품 교체 상담', '보험 처리 문의'],
                    'marketing': ['신차 출시 안내', '할인 이벤트 안내', '정기점검 안내', '멤버십 혜택 안내'],
                    'complaint': ['서비스 불만', '부품 불량 신고', '직원 응대 불만', '대기시간 불만'],
                    'inquiry': ['영업시간 문의', '위치 문의', '서비스 요금 문의', '예약 문의'],
                    'follow_up': ['서비스 후 확인', '만족도 조사', '추가 서비스 안내', '재방문 안내']
                }
                
                title = random.choice(titles[comm_type])
                content = fake.text(max_nb_chars=300)
                
                communications.append(CustomerCommunication(
                    customer=customer,
                    communication_date=timezone.make_aware(fake.date_time_between(start_date='-1y', end_date='now'),
                    communication_type=comm_type,
                    method=method,
                    direction=direction,
                    title=title,
                    content=content,
                    result=result,
                    follow_up_needed=random.choice([True, False]),
                    created_by=admin_user,
                    created_at=timezone.make_aware(fake.date_time_between(start_date='-1y', end_date='now')
                ))
        
        CustomerCommunication.objects.bulk_create(communications, batch_size=100)
        self.stdout.write(f'소통 이력 {len(communications)}건 생성 완료')

    def create_happy_calls(self):
        customers_with_vehicles = list(Customer.objects.filter(
            customer_status='registered',
            vehicle_ownerships__isnull=False
        ).distinct()[:300])
        admin_user = User.objects.first()
        
        happy_calls = []
        
        for customer in customers_with_vehicles:
            # 고객당 0~5개의 해피콜 생성
            num_calls = random.choices([0, 1, 2, 3], weights=[0.3, 0.4, 0.2, 0.1])[0]
            
            for i in range(num_calls):
                call_sequence = random.choice([1, 2, 3])
                scheduled_date = timezone.make_aware(fake.date_time_between(start_date='-6m', end_date='+1m')
                
                # 80% 확률로 완료된 콜
                is_completed = random.random() < 0.8
                completed_date = timezone.make_aware(fake.date_time_between(
                    start_date=scheduled_date, 
                    end_date='now'
                ) if is_completed else None
                
                contact_result = random.choice(['completed', 'no_answer', 'refused']) if is_completed else ''
                satisfaction_score = random.choice([1, 2, 3, 4, 5]) if contact_result == 'completed' else None
                
                complaint_exists = random.choice([True, False]) if satisfaction_score and satisfaction_score <= 3 else False
                complaint_details = fake.text(max_nb_chars=200) if complaint_exists else ''
                
                happy_calls.append(HappyCall(
                    customer=customer,
                    service_record_id=random.randint(1, 1000),  # 가상의 서비스 ID
                    call_sequence=call_sequence,
                    scheduled_date=scheduled_date,
                    completed_date=completed_date,
                    contact_result=contact_result,
                    satisfaction_score=satisfaction_score,
                    complaint_exists=complaint_exists,
                    complaint_details=complaint_details,
                    follow_up_service_needed=random.choice([True, False]),
                    next_call_scheduled=random.choice([True, False]) if call_sequence < 3 else False,
                    notes=fake.text(max_nb_chars=150),
                    created_by=admin_user,
                    created_at=timezone.make_aware(fake.date_time_between(start_date=scheduled_date, end_date='now')
                ))
        
        HappyCall.objects.bulk_create(happy_calls, batch_size=100)
        self.stdout.write(f'해피콜 {len(happy_calls)}건 생성 완료')

    def create_marketing_campaigns(self):
        admin_user = User.objects.first()
        
        campaigns = [
            {
                'name': '2024 신차 출시 기념 이벤트',
                'description': '신차 출시를 기념하여 기존 고객 대상 특별 할인 이벤트',
                'campaign_type': 'sms',
                'start_date': date(2024, 1, 1),
                'end_date': date(2024, 1, 31),
                'status': 'completed'
            },
            {
                'name': '정기점검 안내 캠페인',
                'description': '정기점검 시기가 된 고객들에게 안내 발송',
                'campaign_type': 'phone',
                'start_date': date(2024, 2, 1),
                'end_date': date(2024, 2, 28),
                'status': 'completed'
            },
            {
                'name': '봄맞이 차량관리 이벤트',
                'description': '봄철 차량관리를 위한 종합 점검 서비스 안내',
                'campaign_type': 'dm',
                'start_date': date(2024, 3, 1),
                'end_date': date(2024, 4, 30),
                'status': 'completed'
            },
            {
                'name': 'VIP 고객 감사 이벤트',
                'description': 'VIP 멤버십 고객 대상 특별 혜택 제공',
                'campaign_type': 'email',
                'start_date': date(2024, 6, 1),
                'end_date': date(2024, 6, 30),
                'status': 'active'
            },
            {
                'name': '여름휴가 대비 차량점검',
                'description': '여름휴가철 장거리 운행을 위한 사전 점검 캠페인',
                'campaign_type': 'sms',
                'start_date': date(2024, 7, 1),
                'end_date': date(2024, 8, 31),
                'status': 'draft'
            }
        ]
        
        created_campaigns = []
        for camp_data in campaigns:
            campaign = MarketingCampaign.objects.create(
                name=camp_data['name'],
                description=camp_data['description'],
                campaign_type=camp_data['campaign_type'],
                start_date=camp_data['start_date'],
                end_date=camp_data['end_date'],
                status=camp_data['status'],
                created_by=admin_user,
                created_at=timezone.make_aware(fake.date_time_between(start_date='-6m', end_date='now')
            )
            created_campaigns.append(campaign)
        
        self.stdout.write(f'마케팅 캠페인 {len(created_campaigns)}개 생성 완료')
        
        # 캠페인 이력 생성
        self.create_campaign_history(created_campaigns[:3])  # 완료된 캠페인만

    def create_campaign_history(self, campaigns):
        customers = list(Customer.objects.filter(marketing_consent=True))
        
        campaign_histories = []
        
        for campaign in campaigns:
            # 각 캠페인당 고객의 30~70% 정도에게 발송
            target_customers = random.sample(customers, random.randint(
                int(len(customers) * 0.3), 
                int(len(customers) * 0.7)
            ))
            
            for customer in target_customers:
                sent_date = timezone.make_aware(fake.date_time_between(
                    start_date=campaign.start_date, 
                    end_date=campaign.end_date
                )
                
                delivery_status = random.choices(
                    ['sent', 'failed', 'refused'],
                    weights=[0.85, 0.1, 0.05]
                )[0]
                
                response_type = ''
                roi_amount = 0
                
                if delivery_status == 'sent':
                    response_type = random.choices(
                        ['interested', 'purchased', 'refused', 'no_response'],
                        weights=[0.2, 0.1, 0.05, 0.65]
                    )[0]
                    
                    if response_type == 'purchased':
                        roi_amount = random.randint(100000, 2000000)
                    elif response_type == 'interested':
                        roi_amount = random.randint(0, 500000) if random.random() < 0.3 else 0
                
                campaign_histories.append(CustomerCampaignHistory(
                    customer=customer,
                    campaign=campaign,
                    sent_date=sent_date,
                    delivery_status=delivery_status,
                    response_type=response_type,
                    roi_amount=roi_amount
                ))
        
        CustomerCampaignHistory.objects.bulk_create(campaign_histories, batch_size=100)
        self.stdout.write(f'캠페인 이력 {len(campaign_histories)}건 생성 완료')