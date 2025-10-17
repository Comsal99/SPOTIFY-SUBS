import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

class DataManager:
    """Manages data persistence and operations for the subscription manager."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """Create data directory if it doesn't exist."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def get_data_file_path(self, year: int) -> str:
        """Get the file path for a specific year's data."""
        return os.path.join(self.data_dir, f"subscription_data_{year}.json")
    
    def load_data(self, year: int) -> Dict[str, Any]:
        """Load data for a specific year."""
        file_path = self.get_data_file_path(year)
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        # Return default structure if file doesn't exist or is corrupted
        return {
            "year": year,
            "members": [],
            "payments": {},
            "payment_history": [],
            "settings": {
                "total_price": 100.0,
                "max_slots": 10
            },
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    def save_data(self, year: int, data: Dict[str, Any]):
        """Save data for a specific year."""
        file_path = self.get_data_file_path(year)
        data["updated_at"] = datetime.now().isoformat()
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def get_available_years(self) -> List[int]:
        """Get list of years that have data files."""
        years = []
        
        if not os.path.exists(self.data_dir):
            return years
        
        for filename in os.listdir(self.data_dir):
            if filename.startswith("subscription_data_") and filename.endswith(".json"):
                try:
                    year_str = filename.replace("subscription_data_", "").replace(".json", "")
                    year = int(year_str)
                    years.append(year)
                except ValueError:
                    continue
        
        return sorted(years)
    
    def create_year_data(self, year: int) -> Dict[str, Any]:
        """Create new year data structure."""
        data = self.load_data(year)  # This will create default structure
        self.save_data(year, data)
        return data
    
    def copy_members_from_year(self, source_year: int, target_year: int):
        """Copy member list from one year to another."""
        source_data = self.load_data(source_year)
        target_data = self.load_data(target_year)
        
        # Copy members but not their payments
        target_data["members"] = source_data.get("members", []).copy()
        
        # Initialize empty payments for all copied members
        target_data["payments"] = {}
        for member in target_data["members"]:
            target_data["payments"][member] = {}
        
        self.save_data(target_year, target_data)
    
    def add_member(self, year: int, member_name: str):
        """Add a new member to the specified year."""
        data = self.load_data(year)
        
        if member_name not in data["members"]:
            data["members"].append(member_name)
            data["payments"][member_name] = {}
            self.save_data(year, data)
    
    def remove_member(self, year: int, member_name: str):
        """Remove a member from the specified year."""
        data = self.load_data(year)
        
        if member_name in data["members"]:
            data["members"].remove(member_name)
            if member_name in data["payments"]:
                del data["payments"][member_name]
            self.save_data(year, data)
    
    def update_payment(self, year: int, member_name: str, month: str, paid: bool):
        """Update payment status for a member and month."""
        data = self.load_data(year)
        
        if member_name not in data["payments"]:
            data["payments"][member_name] = {}
        
        # Check if this is a change and log it
        old_status = data["payments"][member_name].get(month, False)
        if old_status != paid:
            # Ensure payment_history exists
            if "payment_history" not in data:
                data["payment_history"] = []
            
            # Add history entry
            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "member": member_name,
                "month": month,
                "action": "marked_paid" if paid else "marked_unpaid",
                "old_status": old_status,
                "new_status": paid
            }
            data["payment_history"].append(history_entry)
        
        data["payments"][member_name][month] = paid
        self.save_data(year, data)
    
    def update_settings(self, year: int, total_price: float, max_slots: int):
        """Update subscription settings for a year."""
        data = self.load_data(year)
        data["settings"]["total_price"] = total_price
        data["settings"]["max_slots"] = max_slots
        self.save_data(year, data)
    
    def get_member_payments(self, year: int, member_name: str) -> Dict[str, bool]:
        """Get payment status for a specific member."""
        data = self.load_data(year)
        return data.get("payments", {}).get(member_name, {})
    
    def bulk_update_payments(self, year: int, member_name: str, months: List[str], paid: bool):
        """Bulk update payment status for multiple months."""
        data = self.load_data(year)
        
        if member_name not in data["payments"]:
            data["payments"][member_name] = {}
        
        for month in months:
            data["payments"][member_name][month] = paid
        
        self.save_data(year, data)
    
    def get_payment_history(self, year: int, member_name: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get payment history for a year, optionally filtered by member."""
        data = self.load_data(year)
        history = data.get("payment_history", [])
        
        # Filter by member if specified
        if member_name:
            history = [h for h in history if h.get("member") == member_name]
        
        # Sort by timestamp (newest first)
        history = sorted(history, key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Limit if specified
        if limit:
            history = history[:limit]
        
        return history
    
    def get_payment_summary(self, year: int) -> Dict[str, Any]:
        """Get overall payment summary for a year."""
        data = self.load_data(year)
        members = data.get("members", [])
        payments = data.get("payments", {})
        settings = data.get("settings", {"total_price": 100.0, "max_slots": 10})
        
        if not members:
            return {
                "total_members": 0,
                "total_possible_amount": 0,
                "total_paid_amount": 0,
                "total_outstanding_amount": 0,
                "overall_payment_rate": 0
            }
        
        price_per_slot = settings["total_price"] / len(members)
        total_possible = len(members) * 12 * price_per_slot
        total_paid = 0
        
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        for member in members:
            member_payments = payments.get(member, {})
            months_paid = sum(1 for month in months if member_payments.get(month, False))
            total_paid += months_paid * price_per_slot
        
        return {
            "total_members": len(members),
            "total_possible_amount": total_possible,
            "total_paid_amount": total_paid,
            "total_outstanding_amount": total_possible - total_paid,
            "overall_payment_rate": (total_paid / total_possible * 100) if total_possible > 0 else 0
        }
    
    def create_full_backup(self) -> str:
        """Create a full backup of all years as JSON string."""
        backup_data = {
            "backup_timestamp": datetime.now().isoformat(),
            "years": {}
        }
        
        for year in self.get_available_years():
            backup_data["years"][str(year)] = self.load_data(year)
        
        return json.dumps(backup_data, indent=2, ensure_ascii=False)
    
    def restore_from_backup(self, backup_json: str) -> tuple[bool, str]:
        """Restore data from backup JSON string."""
        try:
            backup_data = json.loads(backup_json)
            
            if "years" not in backup_data:
                return False, "Invalid backup format: missing 'years' key"
            
            # Restore each year
            restored_years = []
            for year_str, year_data in backup_data["years"].items():
                try:
                    year = int(year_str)
                    self.save_data(year, year_data)
                    restored_years.append(year)
                except (ValueError, KeyError) as e:
                    continue
            
            if restored_years:
                return True, f"Successfully restored {len(restored_years)} year(s): {', '.join(map(str, restored_years))}"
            else:
                return False, "No valid year data found in backup"
                
        except json.JSONDecodeError:
            return False, "Invalid JSON format"
        except Exception as e:
            return False, f"Error during restore: {str(e)}"
