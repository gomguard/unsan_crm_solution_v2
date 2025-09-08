import logging
import re
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger('phone_access')

class AdminPhoneAccessLogMiddleware(MiddlewareMixin):
    """
    관리자의 전화번호 접근을 로깅하는 미들웨어
    """
    
    def process_response(self, request, response):
        # 관리자가 아니거나 익명 사용자면 로깅하지 않음
        if isinstance(request.user, AnonymousUser) or not request.user.is_staff:
            return response
            
        # 응답이 HTML이거나 JSON인 경우에만 체크
        content_type = response.get('Content-Type', '')
        if not ('text/html' in content_type or 'application/json' in content_type):
            return response
            
        # 전화번호 패턴 검색 (한국 전화번호 형식)
        phone_pattern = r'0\d{1,2}-?\d{3,4}-?\d{4}'
        
        try:
            if hasattr(response, 'content'):
                content = response.content.decode('utf-8', errors='ignore')
                phones = re.findall(phone_pattern, content)
                
                if phones:
                    logger.info(
                        f"Phone access by admin - User: {request.user.username} "
                        f"({request.user.get_full_name()}) | "
                        f"URL: {request.get_full_path()} | "
                        f"IP: {self._get_client_ip(request)} | "
                        f"Phone count: {len(phones)}"
                    )
        except Exception as e:
            # 로깅 실패해도 응답은 정상 반환
            logger.error(f"Error in phone access logging: {e}")
            
        return response
    
    def _get_client_ip(self, request):
        """클라이언트 IP 주소 추출"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class PhoneSecurityMiddleware(MiddlewareMixin):
    """
    전화번호 보안 관련 미들웨어
    """
    
    def process_request(self, request):
        # 현재는 특별한 보안 처리 없음
        # 필요시 IP 제한, 접근 빈도 제한 등 구현 가능
        return None