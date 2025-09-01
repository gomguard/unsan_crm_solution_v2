from django.shortcuts import render

def service_list(request):
    return render(request, 'services/service_list.html')
