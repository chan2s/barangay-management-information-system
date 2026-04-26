from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import PublicBlotterForm
from .models import Blotter
from django.http import JsonResponse
from django.db.models import Q

def file_blotter(request):
    if request.method == 'POST':
        form = PublicBlotterForm(request.POST)
        if form.is_valid():
            blotter = form.save()
            return render(request, 'blotter_success.html', {'blotter': blotter})
    else:
        form = PublicBlotterForm()
    
    return render(request, 'file_blotter.html', {'form': form})

def track_blotter(request):
    blotter = None
    searched_number = ''
    
    if request.method == 'POST':
        blotter_number = request.POST.get('blotter_number', '').strip()
        searched_number = blotter_number
        
        if blotter_number:
            try:
                blotter = Blotter.objects.get(blotter_number=blotter_number)
                messages.success(request, f"✅ Blotter found!")
            except Blotter.DoesNotExist:
                messages.error(request, f"❌ No blotter found with number: {blotter_number}")
    
    return render(request, 'track_blotter.html', {
        'blotter': blotter,
        'searched_number': searched_number
    })

def blotter_success(request):
    return render(request, 'blotter_success.html')

def blotter_stats_api(request):
    """API endpoint to get blotter statistics"""
    try:
        total = Blotter.objects.count()
        pending = Blotter.objects.filter(
            Q(status='pending') | Q(status='scheduled') | Q(status='in_progress')
        ).count()
        resolved = Blotter.objects.filter(
            Q(status='resolved') | Q(status='closed')
        ).count()
        
        data = {
            'total': total,
            'pending': pending,
            'resolved': resolved,
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)