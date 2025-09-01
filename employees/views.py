from django.shortcuts import render

def employee_list(request):
    return render(request, 'employees/employee_list.html')
