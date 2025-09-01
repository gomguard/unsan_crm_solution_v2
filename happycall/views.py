from django.shortcuts import render

def happycall_list(request):
    return render(request, 'happycall/happycall_list.html')
