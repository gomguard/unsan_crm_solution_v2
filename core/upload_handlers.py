from django.db import transaction
from django.utils import timezone
from django.core.cache import cache
from datetime import datetime
from customers.models import Customer, Vehicle, CustomerVehicle
from services.models import ServiceType, ServiceRequest
from django.contrib.auth import get_user_model
import logging
import uuid
import pandas as pd
import re

logger = logging.getLogger(__name__)
User = get_user_model()

class DataUploadHandler:
    """데이터 업로드 처리 핸들러"""
    
    def _is_numeric_placeholder(self, value):
        """숫자 형태의 플레이스홀더 값인지 확인 (1.0, 2.0 등)"""
        if not value or pd.isna(value):
            return True
        
        value_str = str(value).strip()
        if not value_str:
            return True
            
        # 정규식으로 순수 숫자(정수 또는 소수)인지 확인
        return bool(re.match(r'^[0-9]+(\.[0-9]+)?$', value_str))

    def __init__(self, upload_type, duplicate_handling, user, progress_key=None):
        self.upload_type = upload_type
        self.duplicate_handling = duplicate_handling
        self.user = user
        self.progress_key = progress_key or str(uuid.uuid4())
        self.results = {
            'success': 0,
            'skipped': 0,
            'updated': 0,
            'errors': 0,
            'error_details': []
        }
        # 초기 진행 상황 설정
        self.update_progress(0, '업로드를 준비하고 있습니다...')
    
    def update_progress(self, percent, message):
        """진행 상황 업데이트"""
        progress_data = {
            'percent': percent,
            'message': message,
            'results': self.results.copy()
        }
        cache.set(f'upload_progress_{self.progress_key}', progress_data, timeout=300)
    
    def get_progress(self):
        """현재 진행 상황 반환"""
        return cache.get(f'upload_progress_{self.progress_key}')
    
    def process_data(self, df):
        """DataFrame 데이터 처리"""
        total_rows = len(df)
        self.update_progress(5, f'총 {total_rows}건의 데이터를 처리합니다...')
        
        if self.upload_type == 'customers':
            return self._process_customers(df)
        elif self.upload_type == 'vehicles':
            return self._process_vehicles(df)
        elif self.upload_type == 'services':
            return self._process_services(df)
        else:
            raise ValueError(f"지원하지 않는 업로드 타입: {self.upload_type}")
    
    def _process_customers(self, df):
        """고객 데이터 처리"""
        total_rows = len(df)
        self.update_progress(10, f'총 {total_rows:,}건의 고객 데이터 처리를 시작합니다...')
        
        # 청크 단위로 처리 (배치 크기: 20개씩으로 축소)
        chunk_size = 20
        processed_count = 0
        
        for chunk_start in range(0, total_rows, chunk_size):
            chunk_end = min(chunk_start + chunk_size, total_rows)
            chunk_df = df.iloc[chunk_start:chunk_end]
            
            try:
                # 청크별로 일괄 처리
                self._process_customer_chunk(chunk_df, chunk_start)
                processed_count = chunk_end
                
            except Exception as e:
                logger.error(f"청크 처리 중 오류 발생 (행 {chunk_start}-{chunk_end}): {e}")
                # 청크 처리 실패 시 개별 처리로 전환
                processed_count = self._process_individual_fallback(chunk_df, chunk_start, chunk_end)
            
            # 진행률 업데이트 (100건마다 또는 청크가 5개 이상일 때만)
            if processed_count % 100 == 0 or (chunk_end - chunk_start) >= 100:
                progress_percent = int(10 + (80 * processed_count / total_rows))
                self.update_progress(
                    progress_percent, 
                    f'고객 데이터 처리 중... ({processed_count:,}/{total_rows:,})'
                )
        
        self.update_progress(95, f'고객 데이터 처리 완료 ({total_rows:,}건)')
        return self.results
    
    def _process_customer_chunk(self, chunk_df, chunk_start):
        """고객 데이터 청크 처리"""
        # 청크 내 모든 전화번호를 한 번에 조회 (성능 최적화)
        phones_in_chunk = [str(row['phone']).strip() for _, row in chunk_df.iterrows()]
        existing_customers = {
            customer.phone: customer 
            for customer in Customer.objects.filter(phone__in=phones_in_chunk)
        }
        
        for index, row in chunk_df.iterrows():
            try:
                with transaction.atomic():  # 각 행을 개별 트랜잭션으로 처리
                    phone = str(row['phone']).strip()
                    
                    # 미리 조회한 딕셔너리에서 찾기 (또는 실시간 재확인)
                    existing = existing_customers.get(phone)
                    if not existing:
                        # 미리 조회했지만 다시 한번 확인 (동시성 문제 방지)
                        existing = Customer.objects.filter(phone=phone).first()
                
                    if existing:
                        if self.duplicate_handling == 'skip':
                            self.results['skipped'] += 1
                            continue
                        elif self.duplicate_handling == 'error':
                            raise ValueError(f"중복된 전화번호: {phone}")
                        elif self.duplicate_handling == 'update':
                            # 기존 고객 정보 업데이트
                            self._update_customer(existing, row)
                            self.results['updated'] += 1
                            continue
                    
                    # 새 고객 생성 (트랜잭션 내에서 안전하게)
                    self._create_customer(row)
                    self.results['success'] += 1
                
            except Exception as e:
                self.results['errors'] += 1
                self.results['error_details'].append(
                    f"행 {chunk_start + index + 2}: {str(e)}"
                )
                logger.error(f"고객 데이터 처리 오류 - 행 {chunk_start + index + 2}: {e}")
    
    def _update_customer(self, existing, row):
        """기존 고객 정보 업데이트"""
        existing.name = row.get('name', existing.name)
        existing.email = row.get('email', existing.email)
        
        # 주소 필드 안전하게 처리 (숫자 형태 플레이스홀더 제거)
        address_main = row.get('address_main', existing.address_main)
        if self._is_numeric_placeholder(address_main):
            address_main = ''
        existing.address_main = address_main
        
        address_detail = row.get('address_detail', existing.address_detail)
        if self._is_numeric_placeholder(address_detail):
            address_detail = ''
        existing.address_detail = address_detail
        existing.customer_type = row.get('customer_type', existing.customer_type)
        existing.membership_status = row.get('membership_status', existing.membership_status)
        existing.customer_grade = row.get('customer_grade', existing.customer_grade)
        existing.business_number = row.get('business_number', existing.business_number)
        existing.company_name = row.get('company_name', existing.company_name)
        
        # 개인정보 동의 처리 (필수)
        if 'privacy_consent' in row and str(row['privacy_consent']).upper() == 'TRUE':
            existing.privacy_consent = True
            if not existing.privacy_consent_date:
                existing.privacy_consent_date = timezone.now()
        
        # 마케팅 동의 처리 (선택)
        if 'marketing_consent' in row:
            marketing_consent = str(row['marketing_consent']).upper() == 'TRUE'
            if marketing_consent != existing.marketing_consent:
                existing.marketing_consent = marketing_consent
                existing.marketing_consent_date = timezone.now()
        
        # 연락거부 처리
        if 'do_not_contact' in row:
            do_not_contact = str(row['do_not_contact']).upper() == 'TRUE'
            if do_not_contact != existing.do_not_contact:
                existing.do_not_contact = do_not_contact
                existing.do_not_contact_date = timezone.now() if do_not_contact else None
        
        existing.notes = row.get('notes', existing.notes)
        existing.save()
    
    def _create_customer(self, row):
        """새 고객 생성"""
        phone = str(row['phone']).strip()
        
        # 개인정보 동의 확인 (필수)
        privacy_consent = str(row.get('privacy_consent', '')).upper() == 'TRUE'
        if not privacy_consent:
            raise ValueError(f"개인정보 처리 동의가 필요합니다: {phone}")
        
        # 주소 필드 안전하게 처리 (숫자 형태 플레이스홀더 제거)
        address_main = row.get('address_main', '')
        if self._is_numeric_placeholder(address_main):
            address_main = ''
        
        address_detail = row.get('address_detail', '')
        if self._is_numeric_placeholder(address_detail):
            address_detail = ''

        customer_data = {
            'name': row['name'],
            'phone': phone,
            'email': row.get('email', ''),
            'address_main': address_main,
            'address_detail': address_detail,
            'customer_status': 'registered',
            'customer_type': row.get('customer_type', 'individual'),
            'membership_status': row.get('membership_status', 'basic'),
            'customer_grade': row.get('customer_grade', 'B'),
            'business_number': row.get('business_number', ''),
            'company_name': row.get('company_name', ''),
            'privacy_consent': True,
            'privacy_consent_date': timezone.now(),
            'notes': row.get('notes', '')
        }
        
        # 마케팅 동의 처리 (선택)
        if str(row.get('marketing_consent', '')).upper() == 'TRUE':
            customer_data['marketing_consent'] = True
            customer_data['marketing_consent_date'] = timezone.now()
        
        # 연락거부 처리
        if str(row.get('do_not_contact', '')).upper() == 'TRUE':
            customer_data['do_not_contact'] = True
            customer_data['do_not_contact_date'] = timezone.now()
        
        # 금지고객 처리 (관리자만 설정 가능)
        if str(row.get('is_banned', '')).upper() == 'TRUE':
            customer_data['is_banned'] = True
            customer_data['banned_date'] = timezone.now()
            customer_data['banned_by'] = self.user
            customer_data['banned_reason'] = '데이터 업로드시 설정'
        
        Customer.objects.create(**customer_data)
    
    def _process_individual_fallback(self, chunk_df, chunk_start, chunk_end):
        """청크 처리 실패 시 개별 처리로 폴백"""
        processed = chunk_start
        for index, row in chunk_df.iterrows():
            try:
                phone = str(row['phone']).strip()
                existing = Customer.objects.filter(phone=phone).first()
                
                if existing:
                    if self.duplicate_handling == 'skip':
                        self.results['skipped'] += 1
                    elif self.duplicate_handling == 'update':
                        self._update_customer(existing, row)
                        self.results['updated'] += 1
                    else:  # error
                        self.results['errors'] += 1
                        self.results['error_details'].append(f"행 {index + 2}: 중복된 전화번호: {phone}")
                else:
                    try:
                        self._create_customer(row)
                        self.results['success'] += 1
                    except Exception as create_error:
                        # 중복으로 인한 에러인 경우 건너뛰기로 처리
                        if 'UNIQUE constraint failed' in str(create_error):
                            self.results['skipped'] += 1
                        else:
                            raise create_error
                    
                processed += 1
                
            except Exception as e:
                self.results['errors'] += 1
                self.results['error_details'].append(f"행 {index + 2}: {str(e)}")
                processed += 1
        
        return min(processed, chunk_end)
    
    def _process_vehicles(self, df):
        """차량 데이터 처리"""
        total_rows = len(df)
        self.update_progress(10, f'총 {total_rows:,}건의 차량 데이터 처리를 시작합니다...')
        
        # 청크 단위로 처리 (크기 축소)
        chunk_size = 20
        processed_count = 0
        
        for chunk_start in range(0, total_rows, chunk_size):
            chunk_end = min(chunk_start + chunk_size, total_rows)
            chunk_df = df.iloc[chunk_start:chunk_end]
            
            try:
                # 청크별로 일괄 처리
                self._process_vehicle_chunk(chunk_df, chunk_start)
                processed_count = chunk_end
                
            except Exception as e:
                logger.error(f"차량 청크 처리 중 오류 발생 (행 {chunk_start}-{chunk_end}): {e}")
                # 청크 처리 실패 시 개별 처리로 전환
                processed_count = self._process_vehicle_individual_fallback(chunk_df, chunk_start, chunk_end)
            
            # 진행률 업데이트 (100건마다만)
            if processed_count % 100 == 0 or (chunk_end - chunk_start) >= 100:
                progress_percent = int(10 + (80 * processed_count / total_rows))
                self.update_progress(
                    progress_percent, 
                    f'차량 데이터 처리 중... ({processed_count:,}/{total_rows:,})'
                )
        
        self.update_progress(95, f'차량 데이터 처리 완료 ({total_rows:,}건)')
        return self.results
    
    def _process_vehicle_chunk(self, chunk_df, chunk_start):
        """차량 데이터 청크 처리"""
        # 청크 내 모든 차량번호를 한 번에 조회 (성능 최적화)
        vehicle_numbers_in_chunk = [str(row['vehicle_number']).strip() for _, row in chunk_df.iterrows()]
        existing_vehicles = {
            vehicle.vehicle_number: vehicle 
            for vehicle in Vehicle.objects.filter(vehicle_number__in=vehicle_numbers_in_chunk)
        }
        
        # 청크 내 모든 고객 전화번호를 한 번에 조회
        customer_phones_in_chunk = [str(row['customer_phone']).strip() for _, row in chunk_df.iterrows()]
        existing_customers = {
            customer.phone: customer 
            for customer in Customer.objects.filter(phone__in=customer_phones_in_chunk)
        }
        
        for index, row in chunk_df.iterrows():
            try:
                vehicle_number = str(row['vehicle_number']).strip()
                customer_phone = str(row['customer_phone']).strip()
                
                # 미리 조회한 딕셔너리에서 고객 찾기
                customer = existing_customers.get(customer_phone)
                if not customer:
                    # 딕셔너리에 없으면 개별 조회 시도
                    customer = Customer.objects.filter(phone=customer_phone).first()
                    if not customer:
                        raise ValueError(f"고객을 찾을 수 없습니다: {customer_phone}")
                
                # 미리 조회한 딕셔너리에서 차량 찾기
                existing = existing_vehicles.get(vehicle_number)
                
                if existing:
                    if self.duplicate_handling == 'skip':
                        self.results['skipped'] += 1
                        continue
                    elif self.duplicate_handling == 'error':
                        raise ValueError(f"중복된 차량번호: {vehicle_number}")
                    elif self.duplicate_handling == 'update':
                        # 기존 차량 정보 업데이트
                        model_name = row.get('model', existing.model)
                        if 'model_detail' in row and row['model_detail']:
                            model_name = f"{model_name} ({row['model_detail']})"
                        
                        existing.model = model_name
                        existing.year = row.get('year', existing.year)
                        
                        existing.save()
                        self.results['updated'] += 1
                        continue
                
                # 새 차량 생성
                # year 필드 안전하게 처리 (NaN 값 체크)
                year_value = row['year']
                if pd.isna(year_value) or str(year_value).strip() == '':
                    year_value = 2020  # 기본값 설정
                else:
                    try:
                        year_value = int(float(year_value))
                    except (ValueError, TypeError):
                        year_value = 2020
                
                # model_detail이 있으면 model 필드에 합쳐서 저장
                model_name = row['model']
                if 'model_detail' in row and row['model_detail']:
                    model_name = f"{model_name} ({row['model_detail']})"
                
                vehicle_data = {
                    'vehicle_number': vehicle_number,
                    'model': model_name,
                    'year': year_value
                }
                
                vehicle = Vehicle.objects.create(**vehicle_data)
                
                # 고객-차량 관계 생성
                CustomerVehicle.objects.get_or_create(
                    customer=customer,
                    vehicle=vehicle,
                    defaults={'start_date': timezone.now().date()}
                )
                
                self.results['success'] += 1
                
            except Exception as e:
                self.results['errors'] += 1
                error_msg = f"행 {chunk_start + index + 2}: {str(e)}"
                self.results['error_details'].append(error_msg)
                logger.error(f"차량 데이터 처리 오류 - {error_msg}")
    
    def _process_services(self, df):
        """서비스 데이터 처리"""
        total_rows = len(df)
        self.update_progress(10, f'총 {total_rows:,}건의 서비스 데이터 처리를 시작합니다...')
        
        # 청크 단위로 처리
        chunk_size = 50
        processed_count = 0
        
        for chunk_start in range(0, total_rows, chunk_size):
            chunk_end = min(chunk_start + chunk_size, total_rows)
            chunk_df = df.iloc[chunk_start:chunk_end]
            
            for index, row in chunk_df.iterrows():
                try:
                    customer_phone = str(row['customer_phone']).strip()
                    vehicle_number = str(row['vehicle_number']).strip()
                    service_type_name = str(row['service_type']).strip()
                    
                    # 고객 찾기
                    try:
                        customer = Customer.objects.get(phone=customer_phone)
                    except Customer.DoesNotExist:
                        raise ValueError(f"고객을 찾을 수 없습니다: {customer_phone}")
                    
                    # 차량 찾기
                    try:
                        vehicle = Vehicle.objects.get(vehicle_number=vehicle_number)
                    except Vehicle.DoesNotExist:
                        raise ValueError(f"차량을 찾을 수 없습니다: {vehicle_number}")
                    
                    # 서비스 타입 찾기 (ID 또는 이름으로)
                    service_type = None
                    try:
                        # 숫자인 경우 ID로 검색
                        if service_type_name.isdigit():
                            service_type = ServiceType.objects.get(id=int(service_type_name))
                        else:
                            # 문자열인 경우 이름으로 검색
                            service_type = ServiceType.objects.get(name=service_type_name)
                    except ServiceType.DoesNotExist:
                        raise ValueError(f"서비스 타입을 찾을 수 없습니다: {service_type_name} (ID: 1-8 또는 서비스명을 입력하세요)")
                    
                    # 서비스 날짜 파싱 (날짜 또는 날짜+시간 모두 지원)
                    service_date_str = str(row['service_date'])
                    service_datetime = None
                    
                    # 다양한 날짜/시간 형식 시도
                    formats_to_try = [
                        '%Y-%m-%d %H:%M:%S',    # 2025-08-11 09:18:22
                        '%Y-%m-%d %H:%M',       # 2025-08-11 09:18
                        '%Y-%m-%d',             # 2025-08-11
                        '%Y.%m.%d %H:%M:%S',    # 2025.08.11 09:18:22
                        '%Y.%m.%d %H:%M',       # 2025.08.11 09:18
                        '%Y.%m.%d',             # 2025.08.11
                    ]
                    
                    for format_str in formats_to_try:
                        try:
                            service_datetime = datetime.strptime(service_date_str, format_str)
                            break
                        except ValueError:
                            continue
                    
                    if not service_datetime:
                        raise ValueError(f"잘못된 날짜 형식: {service_date_str}")
                    
                    # 중복 검사 (같은 고객, 차량, 서비스 타입, 서비스 날짜)
                    existing = ServiceRequest.objects.filter(
                        customer=customer,
                        vehicle=vehicle,
                        service_type=service_type,
                        service_date__date=service_datetime.date()
                    ).first()
                    
                    if existing:
                        if self.duplicate_handling == 'skip':
                            self.results['skipped'] += 1
                            continue
                        elif self.duplicate_handling == 'error':
                            raise ValueError(f"중복된 서비스: {customer_phone} - {service_type_name}")
                        elif self.duplicate_handling == 'update':
                            # 기존 서비스 정보 업데이트
                            existing.status = row.get('status', existing.status)
                            existing.description = row.get('description', existing.description)
                            existing.estimated_price = row.get('price', existing.estimated_price)
                            existing.save()
                            self.results['updated'] += 1
                            continue
                    
                    # 새 서비스 생성
                    service_request = ServiceRequest.objects.create(
                        customer=customer,
                        vehicle=vehicle,
                        service_type=service_type,
                        description=row.get('description', f'{vehicle.model} - {service_type.name}'),
                        status=row.get('status', 'completed'),
                        priority=row.get('priority', 'normal'),
                        estimated_price=row.get('price', service_type.base_price),
                        created_by=self.user,
                        service_date=timezone.make_aware(service_datetime)  # 실제 서비스 실행일
                        # created_at은 현재 시간으로 자동 설정됨
                    )
                    
                    self.results['success'] += 1
                    
                except Exception as e:
                    self.results['errors'] += 1
                    self.results['error_details'].append(
                        f"행 {chunk_start + index + 2}: {str(e)}"
                    )
                    logger.error(f"서비스 데이터 처리 오류 - 행 {chunk_start + index + 2}: {e}")
            
            processed_count = chunk_end
            # 진행률 업데이트 (청크 단위로만)
            progress_percent = int(10 + (80 * processed_count / total_rows))
            self.update_progress(
                progress_percent, 
                f'서비스 데이터 처리 중... ({processed_count:,}/{total_rows:,})'
            )
        
        self.update_progress(95, f'서비스 데이터 처리 완료 ({total_rows:,}건)')
        return self.results
    
    def _process_vehicle_individual_fallback(self, chunk_df, chunk_start, chunk_end):
        """차량 청크 처리 실패 시 개별 처리로 폴백"""
        processed = chunk_start
        for index, row in chunk_df.iterrows():
            try:
                vehicle_number = str(row['vehicle_number']).strip()
                customer_phone = str(row['customer_phone']).strip()
                
                # 고객 찾기
                customer = Customer.objects.filter(phone=customer_phone).first()
                if not customer:
                    raise ValueError(f"고객을 찾을 수 없습니다: {customer_phone}")
                
                existing = Vehicle.objects.filter(vehicle_number=vehicle_number).first()
                
                if existing:
                    if self.duplicate_handling == 'skip':
                        self.results['skipped'] += 1
                    elif self.duplicate_handling == 'update':
                        model_name = row.get('model', existing.model)
                        if 'model_detail' in row and row['model_detail']:
                            model_name = f"{model_name} ({row['model_detail']})"
                        existing.model = model_name
                        existing.year = row.get('year', existing.year)
                        existing.save()
                        self.results['updated'] += 1
                    else:  # error
                        self.results['errors'] += 1
                        self.results['error_details'].append(f"행 {index + 2}: 중복된 차량번호: {vehicle_number}")
                else:
                    # 새 차량 생성
                    # year 필드 안전하게 처리
                    year_value = row['year']
                    if pd.isna(year_value) or str(year_value).strip() == '':
                        year_value = 2020
                    else:
                        try:
                            year_value = int(float(year_value))
                        except (ValueError, TypeError):
                            year_value = 2020
                    
                    # model_detail이 있으면 model 필드에 합쳐서 저장
                    model_name = row['model']
                    if 'model_detail' in row and row['model_detail']:
                        model_name = f"{model_name} ({row['model_detail']})"
                    
                    vehicle_data = {
                        'vehicle_number': vehicle_number,
                        'model': model_name,
                        'year': year_value
                    }
                    
                    vehicle = Vehicle.objects.create(**vehicle_data)
                    CustomerVehicle.objects.get_or_create(
                        customer=customer,
                        vehicle=vehicle,
                        defaults={'start_date': timezone.now().date()}
                    )
                    self.results['success'] += 1
                
                processed += 1
                
            except Exception as e:
                self.results['errors'] += 1
                self.results['error_details'].append(f"행 {index + 2}: {str(e)}")
                processed += 1
        
        return min(processed, chunk_end)