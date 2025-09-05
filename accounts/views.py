from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy

class CustomLoginView(LoginView):
    template_name = 'sign_in.html'
    
    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('core:dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse_lazy('core:dashboard')
    
    def form_invalid(self, form):
        messages.error(self.request, '사용자명 또는 비밀번호가 올바르지 않습니다.')
        return super().form_invalid(form)

@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')
