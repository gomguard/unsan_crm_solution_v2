from django.shortcuts import render

def accounting_list(request):
    return render(request, 'accounting/accounting_list.html')
