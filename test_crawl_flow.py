"""
Test Script for End-to-End Crawl Flow
Tests the complete flow from API endpoints to crawling
"""
import requests
import time
import json
import sys

# Configuration
BASE_URL = "http://localhost:5000/api/v1"
API_KEY = "your-api-key-here"  # Replace with a valid API key

# Headers
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}


def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_start_crawl():
    """Test starting a crawl job"""
    print_section("TEST 1: Start Crawl Job")

    # Request payload
    payload = {
        "site_id": "1",  # Uganda portal
        "options": {
            "max_pages": 5,
            "test_mode": False
        }
    }

    print(f"\nRequest: POST {BASE_URL}/crawl/start")
    print(f"Payload: {json.dumps(payload, indent=2)}")

    # Make request
    response = requests.post(
        f"{BASE_URL}/crawl/start",
        headers=HEADERS,
        json=payload
    )

    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Body:\n{json.dumps(response.json(), indent=2)}")

    if response.status_code == 202:
        print("\n✓ Crawl job started successfully!")
        return response.json()['data']['job_id']
    else:
        print("\n✗ Failed to start crawl job")
        return None


def test_get_job_status(job_id):
    """Test getting job status"""
    print_section(f"TEST 2: Get Job Status ({job_id})")

    print(f"\nRequest: GET {BASE_URL}/crawl/jobs/{job_id}")

    # Make request
    response = requests.get(
        f"{BASE_URL}/crawl/jobs/{job_id}",
        headers=HEADERS
    )

    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Body:\n{json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        print("\n✓ Retrieved job status successfully!")
        return response.json()['data']
    else:
        print("\n✗ Failed to get job status")
        return None


def test_list_jobs():
    """Test listing all jobs"""
    print_section("TEST 3: List All Jobs")

    print(f"\nRequest: GET {BASE_URL}/crawl/jobs?limit=5")

    # Make request
    response = requests.get(
        f"{BASE_URL}/crawl/jobs?limit=5",
        headers=HEADERS
    )

    print(f"\nResponse Status: {response.status_code}")
    data = response.json()

    if response.status_code == 200:
        print(f"\nTotal Jobs: {data['data']['pagination']['total']}")
        print(f"Jobs in this page: {len(data['data']['jobs'])}")

        if data['data']['jobs']:
            print("\nRecent Jobs:")
            for job in data['data']['jobs'][:3]:
                print(f"  - {job['job_id']}: {job['status']} ({job['site_id']})")

        print("\n✓ Listed jobs successfully!")
        return True
    else:
        print("\n✗ Failed to list jobs")
        return False


def monitor_job(job_id, max_attempts=20):
    """Monitor job until completion"""
    print_section(f"TEST 4: Monitor Job Progress ({job_id})")

    print(f"\nMonitoring job status every 5 seconds...")
    print(f"Max attempts: {max_attempts}")

    for attempt in range(max_attempts):
        # Get job status
        response = requests.get(
            f"{BASE_URL}/crawl/jobs/{job_id}",
            headers=HEADERS
        )

        if response.status_code != 200:
            print(f"\n✗ Error getting job status")
            return None

        job = response.json()['data']
        status = job['status']
        progress = job.get('progress_percentage', 0)
        stats = job.get('statistics', {})

        print(f"\n[{attempt + 1}/{max_attempts}] Status: {status} | Progress: {progress:.1f}%")
        print(f"  Pages: {stats.get('pages_crawled', 0)} | "
              f"Datasets: {stats.get('datasets_found', 0)}")

        # Check if completed
        if status in ['completed', 'failed', 'cancelled']:
            print(f"\n✓ Job finished with status: {status}")
            return job

        # Wait before next check
        time.sleep(5)

    print(f"\n⚠ Job still running after {max_attempts} attempts")
    return None


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  WEB CRAWLER END-TO-END FLOW TEST")
    print("=" * 60)

    print("\nThis script will test the complete crawl flow:")
    print("  1. Start a new crawl job")
    print("  2. Get job status")
    print("  3. List all jobs")
    print("  4. Monitor job progress until completion")

    print(f"\nBase URL: {BASE_URL}")
    print(f"API Key: {API_KEY[:10]}..." if len(API_KEY) > 10 else API_KEY)

    # Confirm before starting
    response = input("\nProceed with tests? (y/n): ")
    if response.lower() != 'y':
        print("Tests cancelled")
        sys.exit(0)

    # Test 1: Start crawl
    job_id = test_start_crawl()
    if not job_id:
        print("\n✗ Test failed: Could not start crawl job")
        sys.exit(1)

    # Wait a moment for job to be queued
    time.sleep(2)

    # Test 2: Get job status
    job_data = test_get_job_status(job_id)
    if not job_data:
        print("\n✗ Test failed: Could not get job status")
        sys.exit(1)

    # Test 3: List jobs
    success = test_list_jobs()
    if not success:
        print("\n✗ Test failed: Could not list jobs")
        sys.exit(1)

    # Test 4: Monitor job
    final_job = monitor_job(job_id, max_attempts=20)

    # Summary
    print_section("TEST SUMMARY")

    if final_job:
        print(f"\n✓ All tests completed successfully!")
        print(f"\nFinal Job Status:")
        print(f"  Job ID: {final_job['job_id']}")
        print(f"  Status: {final_job['status']}")
        print(f"  Site: {final_job['site_id']}")
        print(f"  Statistics:")

        stats = final_job.get('statistics', {})
        for key, value in stats.items():
            print(f"    {key}: {value}")

        if final_job['status'] == 'completed':
            print("\n✓ Crawl completed successfully!")
        else:
            print(f"\n⚠ Crawl ended with status: {final_job['status']}")
            if final_job.get('error_message'):
                print(f"  Error: {final_job['error_message']}")

    else:
        print(f"\n⚠ Tests completed but job monitoring timed out")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
