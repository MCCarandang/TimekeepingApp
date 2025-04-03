from django.shortcuts import render

# Create your views here.
def time_entries_list(request):
    context = {}    # Define a context dictionary (add your data here)
    return render(request, 'template_name.html', context)