from django.shortcuts import render

def inventory_list(request):
    return render(request, 'inventory/inventory_list.html')
