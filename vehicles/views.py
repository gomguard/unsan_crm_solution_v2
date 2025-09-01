from django.shortcuts import render

def vehicle_list(request):
    return render(request, 'vehicles/vehicle_list.html')

def vehicle_detail(request, pk):
    return render(request, 'vehicles/vehicle_detail.html', {'pk': pk})
