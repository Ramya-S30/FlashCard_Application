from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Entry, DetailedEntry
from datetime import datetime
from decimal import Decimal

# Register view
def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
        else:
            user = User.objects.create_user(username=username, password=password)
            user.save()
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
    return render(request, 'tracker/register.html')


# Login view
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'tracker/login.html')


# Logout view
@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


# Dashboard view
@login_required
def dashboard(request):
    user_entries = Entry.objects(user_id=request.user.id).order_by('-date')[:10]  # Last 10 entries
    total_salary = sum(entry.salary for entry in user_entries)
    total_budget = sum(entry.budget for entry in user_entries)
    total_expenses = sum(entry.expenses for entry in user_entries)

    # Smart Alert System
    alerts = []

    # Welcome alert for new users
    if len(user_entries) == 0:
        alerts.append({
            'type': 'info',
            'icon': '🎯',
            'title': 'Welcome to Your Finance Tracker!',
            'message': 'Start your financial journey by adding your first entry',
            'action': 'Click "Add Entry" to begin tracking your budget and expenses.'
        })
        return render(request, 'tracker/dashboard.html', {
            'total_salary': 0,
            'total_budget': 0,
            'total_expenses': 0,
            'alerts': alerts,
            'chart_labels': [],
            'chart_budget_data': [],
            'chart_expenses_data': [],
            'avg_budget': 0,
            'avg_expenses': 0,
            'entries': []
        })

    # Basic budget alert
    if total_expenses > total_budget:
        overspend_amount = total_expenses - total_budget
        overspend_percentage = (overspend_amount / total_budget * 100) if total_budget > 0 else 0
        alerts.append({
            'type': 'danger',
            'icon': '🚨',
            'title': 'Budget Exceeded!',
            'message': f'You\'ve overspent by ${overspend_amount:.2f} ({overspend_percentage:.1f}% over budget)',
            'action': 'Review your recent expenses and consider adjusting your spending habits.'
        })

    # Prepare data for chart
    chart_labels = []
    chart_budget_data = []
    chart_expenses_data = []

    for entry in user_entries:
        chart_labels.append(entry.date.strftime('%m/%d'))
        chart_budget_data.append(float(entry.budget))
        chart_expenses_data.append(float(entry.expenses))

    # Calculate averages and trends
    avg_budget = sum(chart_budget_data) / len(chart_budget_data) if chart_budget_data else 0
    avg_expenses = sum(chart_expenses_data) / len(chart_expenses_data) if chart_expenses_data else 0

    # Advanced Smart Alerts
    if len(user_entries) >= 3:
        recent_entries = list(user_entries[:3])

        # Trend analysis
        recent_expenses = [float(entry.expenses) for entry in recent_entries]
        if len(recent_expenses) >= 2:
            expense_trend = recent_expenses[0] - recent_expenses[-1]

            if expense_trend > 0:
                alerts.append({
                    'type': 'warning',
                    'icon': '📈',
                    'title': 'Rising Expenses Trend',
                    'message': f'Your expenses have increased by ${expense_trend:.2f} in recent entries',
                    'action': 'Consider reviewing your spending categories to identify areas for reduction.'
                })
            elif expense_trend < -50:  # Significant decrease
                alerts.append({
                    'type': 'success',
                    'icon': '📉',
                    'title': 'Great Progress!',
                    'message': f'You\'ve reduced expenses by ${abs(expense_trend):.2f} recently',
                    'action': 'Keep up the excellent financial discipline!'
                })

        # High expense ratio alert
        if avg_expenses > 0 and avg_budget > 0:
            expense_ratio = (avg_expenses / avg_budget) * 100
            if expense_ratio > 90:
                alerts.append({
                    'type': 'warning',
                    'icon': '⚠',
                    'title': 'High Expense Ratio',
                    'message': f'You\'re using {expense_ratio:.1f}% of your budget on average',
                    'action': 'Consider increasing your budget or finding ways to reduce expenses.'
                })
            elif expense_ratio < 70:
                alerts.append({
                    'type': 'info',
                    'icon': '💡',
                    'title': 'Budget Opportunity',
                    'message': f'You\'re only using {expense_ratio:.1f}% of your budget',
                    'action': 'Great job! Consider saving the extra or investing in your future.'
                })

    # Savings potential alert
    if total_budget > total_expenses and total_budget > 0:
        savings_amount = total_budget - total_expenses
        savings_percentage = (savings_amount / total_budget) * 100
        if savings_percentage > 20:
            alerts.append({
                'type': 'success',
                'icon': '💰',
                'title': 'Excellent Savings!',
                'message': f'You\'ve saved ${savings_amount:.2f} ({savings_percentage:.1f}% of budget)',
                'action': 'Consider investing these savings or building an emergency fund.'
            })

    # Low budget alert
    if len(user_entries) > 0 and avg_budget < avg_expenses * 0.8:
        alerts.append({
            'type': 'info',
            'icon': '📊',
            'title': 'Budget Review Needed',
            'message': 'Your budget might be too low for your spending patterns',
            'action': 'Consider reviewing and adjusting your budget to be more realistic.'
        })

    # Spending spike detection
    if len(user_entries) >= 5:
        recent_5_expenses = [float(entry.expenses) for entry in user_entries[:5]]
        if len(recent_5_expenses) >= 2:
            latest_expense = recent_5_expenses[0]
            avg_previous_4 = sum(recent_5_expenses[1:]) / 4

            if latest_expense > avg_previous_4 * 1.5:  # 50% spike
                spike_amount = latest_expense - avg_previous_4
                alerts.append({
                    'type': 'warning',
                    'icon': '📊',
                    'title': 'Spending Spike Detected',
                    'message': f'Your latest expense (${latest_expense:.2f}) is ${spike_amount:.2f} higher than your recent average',
                    'action': 'Review what caused this increase and consider if it was planned or if you need to adjust future spending.'
                })

    # Consistent saver recognition
    if len(user_entries) >= 4:
        last_4_entries = list(user_entries[:4])
        consistent_savings = all(entry.budget > entry.expenses for entry in last_4_entries)

        if consistent_savings:
            alerts.append({
                'type': 'success',
                'icon': '🌟',
                'title': 'Consistent Saver!',
                'message': 'You\'ve stayed under budget for your last 4 entries',
                'action': 'Amazing discipline! Consider setting up automatic savings for your surplus.'
            })

    # Monthly milestone alert (if user has been tracking for a while)
    if len(user_entries) >= 10:
        alerts.append({
            'type': 'info',
            'icon': '🏆',
            'title': 'Tracking Milestone',
            'message': f'You\'ve made {len(user_entries)} financial entries - great commitment to tracking!',
            'action': 'Consider reviewing your long-term trends and setting new financial goals.'
        })

    # Smart financial tip based on patterns
    if len(user_entries) >= 3 and avg_budget > 0 and avg_expenses > 0:
        expense_ratio = (avg_expenses / avg_budget) * 100

        if 80 <= expense_ratio <= 90:
            alerts.append({
                'type': 'info',
                'icon': '💡',
                'title': 'Smart Tip: Emergency Fund',
                'message': f'You\'re using {expense_ratio:.1f}% of your budget consistently',
                'action': 'Consider building an emergency fund with your remaining 10-20% budget surplus.'
            })
        elif expense_ratio < 60:
            alerts.append({
                'type': 'success',
                'icon': '💡',
                'title': 'Smart Tip: Investment Opportunity',
                'message': f'You\'re only using {expense_ratio:.1f}% of your budget',
                'action': 'Great savings rate! Consider investing the surplus in index funds or retirement accounts.'
            })

    context = {
        'total_salary': total_salary,
        'total_budget': total_budget,
        'total_expenses': total_expenses,
        'alerts': alerts,
        'chart_labels': chart_labels,
        'chart_budget_data': chart_budget_data,
        'chart_expenses_data': chart_expenses_data,
        'avg_budget': avg_budget,
        'avg_expenses': avg_expenses,
        'entries': user_entries
    }
    return render(request, 'tracker/dashboard.html', context)


# Entry form view
@login_required
def entry_form(request):
    if request.method == 'POST':
        salary = Decimal(request.POST['salary'])
        budget = Decimal(request.POST['budget'])
        expenses = Decimal(request.POST['expenses'])

        Entry(
            user_id=request.user.id,
            username=request.user.username,
            salary=salary,
            budget=budget,
            expenses=expenses,
            date=datetime.now()
        ).save()
        messages.success(request, 'Entry added successfully!')
        return redirect('dashboard')
    return render(request, 'tracker/entry_form.html')


# History view
@login_required
def history(request):
    entries = Entry.objects(user_id=request.user.id).order_by('-date')
    return render(request, 'tracker/history.html', {'entries': entries})


# Detailed Entry form view
@login_required
def detailed_entry_form(request):
    if request.method == 'POST':
        # Get form data
        salary = Decimal(request.POST.get('salary', 0))

        # Budget categories
        budget_education = Decimal(request.POST.get('budget_education', 0))
        budget_entertainment = Decimal(request.POST.get('budget_entertainment', 0))
        budget_housing = Decimal(request.POST.get('budget_housing', 0))
        budget_transport = Decimal(request.POST.get('budget_transport', 0))
        budget_food = Decimal(request.POST.get('budget_food', 0))
        budget_utilities = Decimal(request.POST.get('budget_utilities', 0))
        budget_others = Decimal(request.POST.get('budget_others', 0))

        # Expense categories
        expense_education = Decimal(request.POST.get('expense_education', 0))
        expense_entertainment = Decimal(request.POST.get('expense_entertainment', 0))
        expense_housing = Decimal(request.POST.get('expense_housing', 0))
        expense_transport = Decimal(request.POST.get('expense_transport', 0))
        expense_food = Decimal(request.POST.get('expense_food', 0))
        expense_utilities = Decimal(request.POST.get('expense_utilities', 0))
        expense_others = Decimal(request.POST.get('expense_others', 0))

        # Create detailed entry
        DetailedEntry(
            user_id=request.user.id,
            username=request.user.username,
            salary=salary,
            budget_education=budget_education,
            budget_entertainment=budget_entertainment,
            budget_housing=budget_housing,
            budget_transport=budget_transport,
            budget_food=budget_food,
            budget_utilities=budget_utilities,
            budget_others=budget_others,
            expense_education=expense_education,
            expense_entertainment=expense_entertainment,
            expense_housing=expense_housing,
            expense_transport=expense_transport,
            expense_food=expense_food,
            expense_utilities=expense_utilities,
            expense_others=expense_others,
            date=datetime.now()
        ).save()

        messages.success(request, 'Detailed entry added successfully!')
        return redirect('detailed_dashboard')

    return render(request, 'tracker/detailed_entry_form.html')


# Detailed Dashboard view
@login_required
def detailed_dashboard(request):
    user_entries = DetailedEntry.objects(user_id=request.user.id).order_by('-date')[:10]
    print(f"DEBUG: User={request.user.username}, Entries found={len(user_entries)}")

    if len(user_entries) == 0:
        return render(request, 'tracker/detailed_dashboard.html', {
            'total_salary': 0,
            'total_budget': 0,
            'total_expenses': 0,
            'categories': [],
            'chart_data': {},
            'entries': []
        })

    # Calculate totals
    total_salary = sum(entry.salary for entry in user_entries)
    total_budget = sum(entry.total_budget for entry in user_entries)
    total_expenses = sum(entry.total_expenses for entry in user_entries)

    # Prepare category data for charts
    categories = ['Education', 'Entertainment', 'Housing', 'Transport', 'Food', 'Utilities', 'Others']
    category_budget_totals = []
    category_expense_totals = []
    category_data = []

    category_mapping = ['education', 'entertainment', 'housing', 'transport', 'food', 'utilities', 'others']

    for i, category in enumerate(category_mapping):
        budget_total = sum(getattr(entry, f'budget_{category}') for entry in user_entries)
        expense_total = sum(getattr(entry, f'expense_{category}') for entry in user_entries)
        category_budget_totals.append(float(budget_total))
        category_expense_totals.append(float(expense_total))

        # Create structured data for template
        category_data.append({
            'name': categories[i],
            'budget': float(budget_total),
            'expense': float(expense_total),
            'icon': ['🎓', '🎬', '🏠', '🚗', '🍽', '⚡', '📦'][i]
        })

    # Prepare timeline data
    chart_labels = [entry.date.strftime('%m/%d') for entry in user_entries]
    chart_budget_data = [float(entry.total_budget) for entry in user_entries]
    chart_expenses_data = [float(entry.total_expenses) for entry in user_entries]

    context = {
        'total_salary': total_salary,
        'total_budget': total_budget,
        'total_expenses': total_expenses,
        'categories': categories,
        'category_data': category_data,
        'category_budget_totals': category_budget_totals,
        'category_expense_totals': category_expense_totals,
        'chart_labels': chart_labels,
        'chart_budget_data': chart_budget_data,
        'chart_expenses_data': chart_expenses_data,
        'entries': user_entries
    }

    return render(request, 'tracker/detailed_dashboard.html', context)


# Detailed History view
@login_required
def detailed_history(request):
    entries = DetailedEntry.objects(user_id=request.user.id).order_by('-date')
    return render(request, 'tracker/detailed_history.html', {'entries': entries})
