from django import forms
from django.core.exceptions import ValidationError
import pandas as pd
import io

class DataUploadForm(forms.Form):
    """데이터 업로드 폼"""
    
    UPLOAD_TYPE_CHOICES = [
        ('customers', '고객 데이터'),
        ('vehicles', '차량 데이터'),
        ('services', '서비스 데이터'),
    ]
    
    upload_type = forms.ChoiceField(
        choices=UPLOAD_TYPE_CHOICES,
        label='업로드 타입',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    file = forms.FileField(
        label='파일',
        help_text='Excel (.xlsx) 또는 CSV (.csv) 파일을 업로드해주세요.',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.csv'
        })
    )
    
    duplicate_handling = forms.ChoiceField(
        choices=[
            ('skip', '중복 건너뛰기'),
            ('update', '중복 데이터 업데이트'),
            ('error', '중복 시 오류 발생'),
        ],
        label='중복 처리 방식',
        initial='skip',
        widget=forms.RadioSelect
    )
    
    def clean_file(self):
        file = self.cleaned_data['file']
        
        if not file:
            raise ValidationError('파일을 선택해주세요.')
        
        # 파일 확장자 검사
        if not file.name.lower().endswith(('.xlsx', '.csv')):
            raise ValidationError('Excel(.xlsx) 또는 CSV(.csv) 파일만 업로드 가능합니다.')
        
        # 파일 크기 검사 (50MB 제한)
        if file.size > 50 * 1024 * 1024:
            raise ValidationError('파일 크기는 50MB 이하여야 합니다.')
        
        return file
    
    def process_file(self):
        """파일 데이터를 처리하여 DataFrame으로 반환"""
        file = self.cleaned_data['file']
        upload_type = self.cleaned_data['upload_type']
        
        try:
            # 파일 읽기
            if file.name.lower().endswith('.csv'):
                df = pd.read_csv(io.StringIO(file.read().decode('utf-8-sig')))
            else:
                df = pd.read_excel(file)
            
            # 컬럼 검증
            required_columns = self.get_required_columns(upload_type)
            missing_columns = set(required_columns) - set(df.columns)
            
            if missing_columns:
                raise ValidationError(
                    f'필수 컬럼이 누락되었습니다: {", ".join(missing_columns)}'
                )
            
            return df
            
        except pd.errors.EmptyDataError:
            raise ValidationError('빈 파일입니다.')
        except Exception as e:
            raise ValidationError(f'파일 읽기 오류: {str(e)}')
    
    def get_required_columns(self, upload_type):
        """업로드 타입별 필수 컬럼 정의"""
        if upload_type == 'customers':
            return ['name', 'phone', 'email', 'address_main']
        elif upload_type == 'vehicles':
            return ['vehicle_number', 'model', 'year', 'customer_phone']
        elif upload_type == 'services':
            return ['customer_phone', 'vehicle_number', 'service_type', 'service_date', 'status']
        return []