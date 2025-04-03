from django.shortcuts import render

# Create your views here.
def time_entries_list(request):
    return render(request, 'template_name.html', context)