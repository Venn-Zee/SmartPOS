from .models import Employee


def user_role(request):
    if not request.user.is_authenticated:
        return {}

    # Superuser diperlakukan sebagai manager
    if request.user.is_superuser:
        return {
            'user_position':         'manager',
            'user_position_display': 'Manager',
            'is_full_access':        True,
            'can_manage_products':   True,
            'can_manage_employees':  True,
            'can_view_transactions': True,
            'can_create_transaction':True,
            'can_view_customers':    True,
            'can_view_reports':      True,
            'can_view_stock_report': True,
        }

    try:
        emp = request.user.employee
        position = emp.position
        position_display = emp.get_position_display()
    except Employee.DoesNotExist:
        position = 'cashier'
        position_display = 'Kasir'

    FULL_ACCESS = position in ('manager', 'supervisor')

    return {
        'user_position':          position,
        'user_position_display':  position_display,
        'is_full_access':         FULL_ACCESS,
        'can_manage_products':    FULL_ACCESS,
        'can_manage_employees':   FULL_ACCESS,
        'can_view_transactions':  position in ('manager', 'supervisor', 'cashier', 'waiter'),
        'can_create_transaction': position in ('manager', 'supervisor', 'cashier', 'waiter'),
        'can_view_customers':     position in ('manager', 'supervisor', 'cashier'),
        'can_view_reports':       FULL_ACCESS,
        'can_view_stock_report':  position in ('manager', 'supervisor', 'barista'),
    }
