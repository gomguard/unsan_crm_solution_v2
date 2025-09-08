from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from pathlib import Path
import os
import pandas as pd
from core.upload_handlers import DataUploadHandler
from django.contrib.auth import get_user_model
import time
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

User = get_user_model()

class Command(BaseCommand):
    help = 'Import data files directly from the data/ folder'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Specific file to import (optional, if not provided will process all files)',
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['customers', 'vehicles', 'services'],
            help='Data type to import (required if --file is provided)',
        )
        parser.add_argument(
            '--duplicates',
            type=str,
            choices=['skip', 'update', 'error'],
            default='skip',
            help='How to handle duplicates (default: skip)',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Username to use for the import (default: first superuser)',
        )

    def handle(self, *args, **options):
        # 데이터 폴더 경로
        data_dir = settings.BASE_DIR / 'data'
        
        if not data_dir.exists():
            raise CommandError(f'데이터 폴더가 존재하지 않습니다: {data_dir}')

        # 사용자 설정
        if options['user']:
            try:
                user = User.objects.get(username=options['user'])
            except User.DoesNotExist:
                raise CommandError(f'사용자를 찾을 수 없습니다: {options["user"]}')
        else:
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                raise CommandError('관리자 사용자가 없습니다. --user 옵션을 사용하세요.')

        self.stdout.write(f'데이터 가져오기 시작 (사용자: {user.username})')
        
        # 특정 파일 처리
        if options['file']:
            if not options['type']:
                raise CommandError('--file 옵션 사용 시 --type 옵션이 필요합니다.')
            
            file_path = data_dir / options['file']
            if not file_path.exists():
                raise CommandError(f'파일을 찾을 수 없습니다: {file_path}')
            
            self.import_file(file_path, options['type'], options['duplicates'], user)
        else:
            # 모든 파일 자동 처리
            self.auto_import_all(data_dir, options['duplicates'], user)

    def auto_import_all(self, data_dir, duplicate_handling, user):
        """데이터 폴더의 모든 파일을 자동으로 가져오기"""
        
        # 파일 타입 매핑 (파일명에서 타입 추정)
        file_patterns = {
            'customers': ['customer', 'client', '고객'],
            'vehicles': ['vehicle', 'car', '차량', '자동차'],
            'services': ['service', 'repair', '서비스', '수리']
        }
        
        processed_files = []
        
        # 지원 파일 확장자
        supported_extensions = ['.xlsx', '.xls', '.csv']
        
        for file_path in data_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                filename_lower = file_path.stem.lower()
                
                # 파일명에서 타입 추정
                detected_type = None
                for data_type, patterns in file_patterns.items():
                    for pattern in patterns:
                        if pattern in filename_lower:
                            detected_type = data_type
                            break
                    if detected_type:
                        break
                
                if detected_type:
                    self.stdout.write(f'\\n파일 처리 중: {file_path.name} (타입: {detected_type})')
                    try:
                        self.import_file(file_path, detected_type, duplicate_handling, user)
                        processed_files.append((file_path.name, detected_type, 'Success'))
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f'파일 처리 실패: {file_path.name} - {str(e)}')
                        )
                        processed_files.append((file_path.name, detected_type, f'Error: {str(e)}'))
                else:
                    self.stdout.write(
                        self.style.WARNING(f'타입을 추정할 수 없는 파일: {file_path.name} (건너뜀)')
                    )
                    processed_files.append((file_path.name, 'Unknown', 'Skipped'))
        
        # 결과 요약
        self.stdout.write('\\n' + '='*50)
        self.stdout.write('처리 결과 요약:')
        self.stdout.write('='*50)
        
        for filename, data_type, status in processed_files:
            status_style = self.style.SUCCESS if status == 'Success' else (
                self.style.WARNING if status == 'Skipped' else self.style.ERROR
            )
            self.stdout.write(f'{filename:<30} | {data_type:<10} | {status_style(status)}')

    def import_file(self, file_path, data_type, duplicate_handling, user):
        """단일 파일 가져오기"""
        start_time = time.time()
        
        # 파일 읽기
        try:
            if file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path, encoding='utf-8')
            else:
                df = pd.read_excel(file_path)
        except UnicodeDecodeError:
            # CSV 인코딩 문제 시 다른 인코딩 시도
            if file_path.suffix.lower() == '.csv':
                try:
                    df = pd.read_csv(file_path, encoding='cp949')
                except:
                    df = pd.read_csv(file_path, encoding='euc-kr')
            else:
                raise
        
        total_rows = len(df)
        self.stdout.write(f'파일 읽기 완료: {total_rows}개 레코드')
        
        # DataUploadHandler 사용
        progress_key = f'import_{int(time.time())}'
        handler = DataUploadHandler(
            upload_type=data_type,
            duplicate_handling=duplicate_handling,
            user=user,
            progress_key=progress_key
        )
        
        # tqdm 진행률 표시 설정
        if HAS_TQDM:
            pbar = tqdm(total=100, desc=f'{data_type.title()} 처리', 
                       bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}] {postfix}')
            
            def progress_callback(percent, message, results=None):
                # tqdm 업데이트
                if percent > pbar.n:
                    pbar.n = percent
                    pbar.set_postfix_str(message)
                    pbar.refresh()
                
                if percent == 100:
                    pbar.close()
        else:
            # tqdm이 없는 경우 기본 진행률 표시
            def progress_callback(percent, message, results=None):
                # 간단한 진행률 바 만들기
                bar_length = 50
                filled_length = int(bar_length * percent // 100)
                bar = '█' * filled_length + '-' * (bar_length - filled_length)
                self.stdout.write(f'\\r[{bar}] {percent:3.0f}% - {message}', ending='')
                if percent == 100:
                    self.stdout.write('')  # 새 줄
        
        # 원래 진행률 업데이트 메서드 백업
        original_update_progress = handler.update_progress
        
        # 진행률 업데이트를 콘솔 출력으로 변경
        handler.update_progress = progress_callback
        
        try:
            # 데이터 처리
            results = handler.process_data(df)
            
            elapsed_time = time.time() - start_time
            
            # 결과 출력
            self.stdout.write(self.style.SUCCESS('\\n처리 완료!'))
            self.stdout.write(f'처리 시간: {elapsed_time:.2f}초')
            self.stdout.write(f'총 레코드: {total_rows}개')
            self.stdout.write(f'성공: {results["success"]}개')
            if results['updated'] > 0:
                self.stdout.write(f'업데이트: {results["updated"]}개')
            if results['skipped'] > 0:
                self.stdout.write(f'건너뜀: {results["skipped"]}개')
            if results['errors'] > 0:
                self.stdout.write(f'오류: {results["errors"]}개')
                if results['error_details']:
                    self.stdout.write('오류 상세:')
                    for error in results['error_details'][:5]:  # 최대 5개만 표시
                        self.stdout.write(f'  - {error}')
                    if len(results['error_details']) > 5:
                        self.stdout.write(f'  ... 외 {len(results["error_details"]) - 5}개')
        
        except Exception as e:
            # 원래 메서드 복원
            handler.update_progress = original_update_progress
            raise CommandError(f'데이터 처리 중 오류: {str(e)}')
        
        # 원래 메서드 복원
        handler.update_progress = original_update_progress