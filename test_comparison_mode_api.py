"""
Test the comparison mode API endpoint
"""
import requests

# Test configuration
BASE_URL = "http://localhost:5002"
REFERENCE_ID = "MRG_006"  # Update with your actual session ID
CHANGE_ID = 1  # Update with your actual change ID

def test_comparison_modes():
    """Test all comparison modes"""
    modes = ['auto', 'vendor_vs_customer', 'base_vs_vendor', 'base_vs_customer']
    
    for mode in modes:
        print(f"\n{'='*60}")
        print(f"Testing mode: {mode}")
        print('='*60)
        
        url = f"{BASE_URL}/merge/{REFERENCE_ID}/changes/{CHANGE_ID}/comparison"
        params = {'mode': mode}
        
        try:
            response = requests.get(url, params=params)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Object Type: {data.get('object_type')}")
                print(f"Old Label: {data.get('old_label')}")
                print(f"New Label: {data.get('new_label')}")
                print(f"Comparison Type: {data.get('comparison_type')}")
                print("✓ Success")
            else:
                print(f"Error: {response.text}")
                print("✗ Failed")
                
        except Exception as e:
            print(f"Exception: {e}")
            print("✗ Failed")

if __name__ == '__main__':
    print("Testing Comparison Mode API")
    print(f"Base URL: {BASE_URL}")
    print(f"Reference ID: {REFERENCE_ID}")
    print(f"Change ID: {CHANGE_ID}")
    test_comparison_modes()
