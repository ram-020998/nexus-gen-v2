"""
Test API Endpoints for AI Summary Feature

This script tests the three new API endpoints added in Phase 5:
1. GET /merge/<reference_id>/summary-progress
2. POST /merge/<reference_id>/regenerate-summaries
3. POST /merge/change/<change_id>/regenerate-summary
"""
import requests
import time
import json


BASE_URL = "http://localhost:5002"


def test_summary_progress(reference_id):
    """Test the summary progress endpoint"""
    print("\n" + "="*60)
    print("TEST 1: Get Summary Progress")
    print("="*60)
    
    url = f"{BASE_URL}/merge/{reference_id}/summary-progress"
    print(f"GET {url}")
    
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Success!")
            print(f"\nProgress Data:")
            print(json.dumps(data, indent=2))
            
            progress = data.get('data', {})
            print(f"\nSummary:")
            print(f"  Total: {progress.get('total', 0)}")
            print(f"  Completed: {progress.get('completed', 0)}")
            print(f"  Processing: {progress.get('processing', 0)}")
            print(f"  Failed: {progress.get('failed', 0)}")
            print(f"  Pending: {progress.get('pending', 0)}")
            print(f"  Percentage: {progress.get('percentage', 0)}%")
            
            return True
        else:
            print(f"✗ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_regenerate_all_summaries(reference_id):
    """Test the regenerate all summaries endpoint"""
    print("\n" + "="*60)
    print("TEST 2: Regenerate All Summaries")
    print("="*60)
    
    url = f"{BASE_URL}/merge/{reference_id}/regenerate-summaries"
    print(f"POST {url}")
    
    try:
        response = requests.post(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Success!")
            print(f"\nResponse:")
            print(json.dumps(data, indent=2))
            return True
        else:
            print(f"✗ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_regenerate_single_summary(change_id):
    """Test the regenerate single summary endpoint"""
    print("\n" + "="*60)
    print("TEST 3: Regenerate Single Summary")
    print("="*60)
    
    url = f"{BASE_URL}/merge/change/{change_id}/regenerate-summary"
    print(f"POST {url}")
    
    try:
        response = requests.post(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Success!")
            print(f"\nResponse:")
            print(json.dumps(data, indent=2))
            return True
        else:
            print(f"✗ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_progress_polling(reference_id, duration=10):
    """Test progress polling over time"""
    print("\n" + "="*60)
    print("TEST 4: Progress Polling (Real-time Updates)")
    print("="*60)
    print(f"Polling for {duration} seconds...")
    
    url = f"{BASE_URL}/merge/{reference_id}/summary-progress"
    
    start_time = time.time()
    poll_count = 0
    
    while time.time() - start_time < duration:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                progress = data.get('data', {})
                
                poll_count += 1
                print(f"\nPoll #{poll_count} ({int(time.time() - start_time)}s):")
                print(f"  Completed: {progress.get('completed', 0)}/{progress.get('total', 0)} "
                      f"({progress.get('percentage', 0)}%)")
                print(f"  Processing: {progress.get('processing', 0)}")
                print(f"  Failed: {progress.get('failed', 0)}")
                print(f"  Pending: {progress.get('pending', 0)}")
                
                # Stop if all done
                if progress.get('processing', 0) == 0 and progress.get('pending', 0) == 0:
                    print("\n✓ All summaries completed!")
                    break
            
            time.sleep(3)  # Poll every 3 seconds
            
        except Exception as e:
            print(f"✗ Error during polling: {e}")
            break
    
    print(f"\nPolling complete. Total polls: {poll_count}")


def main():
    """Run all tests"""
    print("="*60)
    print("AI Summary API Endpoints Test Suite")
    print("="*60)
    print("\nNOTE: Make sure the Flask app is running on port 5002")
    print("      and you have a valid merge session created.")
    
    # Get test parameters
    reference_id = input("\nEnter merge session reference ID (e.g., MRG_001): ").strip()
    
    if not reference_id:
        print("✗ No reference ID provided. Exiting.")
        return
    
    # Test 1: Get progress
    test_summary_progress(reference_id)
    
    # Test 2: Regenerate all (optional)
    regenerate_all = input("\nDo you want to test regenerate all summaries? (y/n): ").strip().lower()
    if regenerate_all == 'y':
        test_regenerate_all_summaries(reference_id)
        
        # Test 4: Poll progress after regeneration
        poll = input("\nDo you want to poll progress for 30 seconds? (y/n): ").strip().lower()
        if poll == 'y':
            test_progress_polling(reference_id, duration=30)
    
    # Test 3: Regenerate single (optional)
    regenerate_single = input("\nDo you want to test regenerate single summary? (y/n): ").strip().lower()
    if regenerate_single == 'y':
        change_id = input("Enter change ID: ").strip()
        if change_id.isdigit():
            test_regenerate_single_summary(int(change_id))
        else:
            print("✗ Invalid change ID")
    
    print("\n" + "="*60)
    print("Test Suite Complete")
    print("="*60)


if __name__ == "__main__":
    main()
