# Copyright (c) 2025, KAINOTOMO PH LTD and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import requests
from invoice2erpnext.utils import format_currency_value

class Invoice2ErpnextSettings(Document):
    """Settings for Invoice2ERPNext integration"""
    
    # Define as class variable - available to all instances and methods
    BASE_URL = "https://kainotomo.com"
    
    @frappe.whitelist()
    def get_credits(self):
        """Test connection to ERPNext API and fetch user credits"""
        
        # Check if integration is enabled
        if hasattr(self, 'enabled') and self.enabled == 0:
            return {
                "success": False,
                "message": "Integration is disabled. Please enable it in settings."
            }
        
        try:
            api_key = self.get_password('api_key')
            api_secret = self.get_password('api_secret') if hasattr(self, 'get_password') else self.api_secret
            
            # Prepare API request headers with decrypted credentials
            headers = {
                "Authorization": f"token {api_key}:{api_secret}",
                "Content-Type": "application/json"
            }
            
            # Make request to the get_user_credits endpoint
            endpoint = f"{self.BASE_URL}/api/method/doc2sys.doc2sys.doctype.doc2sys_user_settings.doc2sys_user_settings.get_user_credits"
            
            # You might need to pass specific user information if required
            data = {}
            if hasattr(self, 'erpnext_user') and self.erpnext_user:
                data = {"user": self.erpnext_user}
            
            # Make the API request
            response = requests.post(
                endpoint,
                headers=headers,
                json=data
            )
            
            # Process the response
            if response.status_code == 200:
                result = response.json()
                
                # If API call was successful
                if result.get("message") and result["message"].get("success"):
                    # Extract credits from response
                    credits = result["message"].get("credits", 0)
                    
                    # Use the utility function to format credits
                    formatted_credits = format_currency_value(credits)
                    
                    return {
                        "success": True,
                        "credits": formatted_credits,
                        "message": "Successfully connected to ERPNext API"
                    }
                else:
                    error_msg = result.get("message", {}).get("message", "API returned error")
                    return {
                        "success": False,
                        "message": f"API Error: {error_msg}"
                    }
            else:
                # Handle HTTP errors
                return {
                    "success": False,
                    "message": f"HTTP Error: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            frappe.log_error(f"ERPNext API Connection Error: {str(e)}", "Invoice2ERPNext")
            return {
                "success": False,
                "message": f"Connection Error: {str(e)}"
            }

    @frappe.whitelist()
    def test_connection(self):
        """Test the connection to the ERPNext API"""
        self.enabled = 1
        result = self.get_credits()
        if result.get("success"):
            self.enabled = 1
        else:
            self.enabled = 0
        
        self.save()

        return result


# Add a global function that doesn't require document permissions
@frappe.whitelist(allow_guest=False)
def get_available_credits():
    """Get available credits - accessible to all authenticated users"""
    try:
        # Check if settings exists - don't need document permissions for this check
        if not frappe.db.exists("Invoice2Erpnext Settings", "Invoice2Erpnext Settings"):
            return {
                "value": 0,
                "fieldtype": "Currency",
            }
        
        # Get the document properly using get_doc which will handle encrypted fields correctly
        settings = frappe.get_doc("Invoice2Erpnext Settings", "Invoice2Erpnext Settings")
        settings.flags.ignore_permissions = True
        
        # Get credits using the instance method which handles credentials properly
        result = settings.get_credits()
        
        # Extract credits from result if successful
        credits = 0
        if result.get("success") and "credits" in result:
            credits = result["credits"]
        
        # Return formatted response for number card
        return {
            "value": credits,
            "fieldtype": "Currency",
        }
    except Exception as e:
        frappe.log_error(f"Error fetching credits for all users: {str(e)}", "Invoice2Erpnext Credits")
        return {
            "value": 0,
            "fieldtype": "Currency",
        }