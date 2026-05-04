from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from Blotter_Module.models import Blotter, Schedule
from staff_module.models import Staff

@login_required(login_url='login')
def kapitan_dashboard(request):
    """Kapitan Dashboard - only shows hearing schedules/appointments"""
    try:
        staff_profile = request.user.staff_profile
        
        # Verify user is Kapitan
        if staff_profile.role != 'kapitan':
            messages.error(request, 'Access denied. Kapitan only area.')
            return redirect('staff_module:staff_dashboard')
        
        # Today's hearings (appointments today)
        today_hearings = Schedule.objects.filter(
            hearing_date__date=timezone.now().date(),
            is_completed=False
        ).select_related('blotter')
        
        # Upcoming hearings (future appointments)
        upcoming_hearings = Schedule.objects.filter(
            hearing_date__gt=timezone.now(),
            is_completed=False
        ).select_related('blotter').order_by('hearing_date')
        
        # Past hearings (completed)
        past_hearings = Schedule.objects.filter(
            hearing_date__lt=timezone.now(),
            is_completed=True
        ).select_related('blotter').order_by('-hearing_date')[:10]
        
        # Count statistics
        total_hearings = Schedule.objects.count()
        pending_hearings = Schedule.objects.filter(is_completed=False, hearing_date__gt=timezone.now()).count()
        completed_hearings = Schedule.objects.filter(is_completed=True).count()
        
        context = {
            'staff': staff_profile,
            'user': request.user,
            'today_hearings': today_hearings,
            'upcoming_hearings': upcoming_hearings,
            'past_hearings': past_hearings,
            'total_hearings': total_hearings,
            'pending_hearings': pending_hearings,
            'completed_hearings': completed_hearings,
        }
        return render(request, 'kapitan_portal/dashboard.html', context)
        
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied. Staff only area.')
        return redirect('dashboard')

@login_required
def hearing_detail(request, hearing_id):
    """View details of a specific hearing appointment"""
    try:
        staff_profile = request.user.staff_profile
        if staff_profile.role != 'kapitan':
            messages.error(request, 'Access denied.')
            return redirect('staff_module:staff_dashboard')
        
        hearing = get_object_or_404(Schedule, id=hearing_id)
        
        context = {
            'hearing': hearing,
            'blotter': hearing.blotter,
            'staff': staff_profile,
            'user': request.user,
        }
        return render(request, 'kapitan_portal/hearing_detail.html', context)
        
    except Staff.DoesNotExist:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')