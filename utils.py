from typing import Dict, Any

def format_currency(amount: float, currency_symbol: str = "$") -> str:
    """Format amount as currency string."""
    return f"{currency_symbol}{amount:.2f}"

def calculate_member_summary(member_payments: Dict[str, bool], price_per_slot: float) -> Dict[str, Any]:
    """Calculate summary statistics for a member."""
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    months_paid = sum(1 for month in months if member_payments.get(month, False))
    months_unpaid = 12 - months_paid
    amount_paid = months_paid * price_per_slot
    amount_owed = months_unpaid * price_per_slot
    payment_rate = (months_paid / 12) * 100 if months_paid > 0 else 0
    
    return {
        "months_paid": months_paid,
        "months_unpaid": months_unpaid,
        "amount_paid": amount_paid,
        "amount_owed": amount_owed,
        "payment_rate": payment_rate
    }

def get_payment_status_color(paid: bool) -> str:
    """Get color for payment status display."""
    return "green" if paid else "red"

def validate_member_name(name: str) -> tuple[bool, str]:
    """Validate member name input."""
    name = name.strip()
    
    if not name:
        return False, "Member name cannot be empty."
    
    if len(name) > 50:
        return False, "Member name must be 50 characters or less."
    
    # Check for invalid characters
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in invalid_chars:
        if char in name:
            return False, f"Member name cannot contain '{char}' character."
    
    return True, ""

def get_month_number(month_name: str) -> int:
    """Convert month name to number (1-12)."""
    months = {
        "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4,
        "May": 5, "Jun": 6, "Jul": 7, "Aug": 8,
        "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
    }
    return months.get(month_name, 1)

def get_month_name(month_number: int) -> str:
    """Convert month number to name."""
    months = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]
    return months[month_number - 1] if 1 <= month_number <= 12 else "Jan"

def calculate_bulk_payment_months(start_month: str, num_months: int) -> list[str]:
    """Calculate which months to mark as paid for bulk payment."""
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    try:
        start_idx = months.index(start_month)
    except ValueError:
        start_idx = 0
    
    selected_months = []
    for i in range(num_months):
        month_idx = (start_idx + i) % 12
        selected_months.append(months[month_idx])
    
    return selected_months

def export_data_to_csv(data: Dict[str, Any]) -> str:
    """Export data to CSV format string."""
    import io
    import csv
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    header = ["Member"] + months + ["Months Paid", "Amount Paid", "Amount Owed"]
    writer.writerow(header)
    
    # Write data
    members = data.get("members", [])
    payments = data.get("payments", {})
    settings = data.get("settings", {"total_price": 100.0})
    
    if members:
        price_per_slot = settings["total_price"] / len(members)
        
        for member in members:
            member_payments = payments.get(member, {})
            row = [member]
            
            # Add month status
            months_paid = 0
            for month in months:
                paid = member_payments.get(month, False)
                row.append("Yes" if paid else "No")
                if paid:
                    months_paid += 1
            
            # Add summary
            amount_paid = months_paid * price_per_slot
            amount_owed = (12 - months_paid) * price_per_slot
            row.extend([months_paid, f"${amount_paid:.2f}", f"${amount_owed:.2f}"])
            
            writer.writerow(row)
    
    return output.getvalue()
