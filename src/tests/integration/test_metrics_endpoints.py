#!/usr/bin/env python3
"""
Comprehensive test suite for HappyRobot Metrics API endpoints
"""

from typing import Optional

import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings for self-signed certificate
urllib3.disable_warnings(InsecureRequestWarning)

BASE_URL = "https://localhost"
API_KEY = "00c8c672-cd17-4b7e-adde-42775aaac89e"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}


class MetricsEndpointTester:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0

    def log_test(self, test_name: str, passed: bool, details: Optional[str] = None):
        self.results.append(
            {
                "test": test_name,
                "result": "PASS" if passed else "FAIL",
                "details": details,
            }
        )
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        print(f"{'PASS' if passed else 'FAIL'} - {test_name}")
        if details and not passed:
            print(f"   Details: {details}")

    def test_get_all_metrics(self):
        """Test GET /api/v1/metrics/call without filters"""
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/metrics/call", headers=HEADERS, verify=False
            )

            # Test status code
            self.log_test(
                "GET /api/v1/metrics/call - Status Code",
                response.status_code == 200,
                f"Got {response.status_code}",
            )

            if response.status_code != 200:
                return

            data = response.json()

            # Test response structure
            required_fields = ["metrics", "total_count", "start_date", "end_date"]
            for field in required_fields:
                self.log_test(
                    f"GET /api/v1/metrics/call - Has {field} field",
                    field in data,
                    f"Missing field: {field}",
                )

            # Test metrics array structure
            if "metrics" in data and data["metrics"]:
                metric = data["metrics"][0]
                metric_fields = [
                    "metrics_id",
                    "transcript",
                    "response",
                    "created_at",
                    "updated_at",
                ]
                for field in metric_fields:
                    self.log_test(
                        f"GET /api/v1/metrics/call - Metric has {field} field",
                        field in metric,
                        f"Missing field: {field}",
                    )

            # Validate total_count is correct
            if "metrics" in data and "total_count" in data:
                actual_count = len(data["metrics"])
                self.log_test(
                    "GET /api/v1/metrics/call - Total count accuracy",
                    actual_count <= data["total_count"],
                    f"Returned {actual_count} items but total_count is {data['total_count']}",
                )

        except Exception as e:
            self.log_test("GET /api/v1/metrics/call - Request", False, str(e))

    def test_get_metrics_with_date_filters(self):
        """Test GET /api/v1/metrics/call with date range filters"""
        try:
            start_date = "2025-08-21T16:00:00Z"
            end_date = "2025-08-21T17:00:00Z"

            response = requests.get(
                f"{BASE_URL}/api/v1/metrics/call?start_date={start_date}&end_date={end_date}",
                headers=HEADERS,
                verify=False,
            )

            self.log_test(
                "GET /api/v1/metrics/call with date filters - Status Code",
                response.status_code == 200,
                f"Got {response.status_code}",
            )

            if response.status_code != 200:
                return

            data = response.json()

            # Verify date filters are reflected in response
            self.log_test(
                "GET /api/v1/metrics/call with date filters - Start date in response",
                data.get("start_date") == start_date,
            )
            self.log_test(
                "GET /api/v1/metrics/call with date filters - End date in response",
                data.get("end_date") == end_date,
            )

        except Exception as e:
            self.log_test(
                "GET /api/v1/metrics/call with date filters - Request", False, str(e)
            )

    def test_get_metrics_with_pagination(self):
        """Test GET /api/v1/metrics/call with pagination limits"""
        try:
            limit = 2
            response = requests.get(
                f"{BASE_URL}/api/v1/metrics/call?limit={limit}",
                headers=HEADERS,
                verify=False,
            )

            self.log_test(
                "GET /api/v1/metrics/call with pagination - Status Code",
                response.status_code == 200,
                f"Got {response.status_code}",
            )

            if response.status_code != 200:
                return

            data = response.json()

            # Verify pagination limit is respected
            if "metrics" in data:
                actual_returned = len(data["metrics"])
                self.log_test(
                    "GET /api/v1/metrics/call with pagination - Limit respected",
                    actual_returned <= limit,
                    f"Requested {limit}, got {actual_returned}",
                )

        except Exception as e:
            self.log_test(
                "GET /api/v1/metrics/call with pagination - Request", False, str(e)
            )

    def test_get_metrics_by_valid_id(self):
        """Test GET /api/v1/metrics/call/{id} with valid ID"""
        try:
            # First get a valid ID
            response = requests.get(
                f"{BASE_URL}/api/v1/metrics/call?limit=1", headers=HEADERS, verify=False
            )
            if response.status_code != 200 or not response.json().get("metrics"):
                self.log_test(
                    "GET /api/v1/metrics/call/{id} with valid ID - Setup",
                    False,
                    "Cannot get valid ID for testing",
                )
                return

            valid_id = response.json()["metrics"][0]["metrics_id"]

            # Test with valid ID
            response = requests.get(
                f"{BASE_URL}/api/v1/metrics/call/{valid_id}",
                headers=HEADERS,
                verify=False,
            )

            self.log_test(
                "GET /api/v1/metrics/call/{id} with valid ID - Status Code",
                response.status_code == 200,
                f"Got {response.status_code}",
            )

            if response.status_code != 200:
                return

            data = response.json()

            # Verify response structure
            required_fields = [
                "metrics_id",
                "transcript",
                "response",
                "created_at",
                "updated_at",
            ]
            for field in required_fields:
                self.log_test(
                    f"GET /api/v1/metrics/call/{{id}} - Has {field} field",
                    field in data,
                    f"Missing field: {field}",
                )

            # Verify the returned ID matches requested ID
            self.log_test(
                "GET /api/v1/metrics/call/{id} - ID matches request",
                data.get("metrics_id") == valid_id,
            )

        except Exception as e:
            self.log_test(
                "GET /api/v1/metrics/call/{id} with valid ID - Request", False, str(e)
            )

    def test_get_metrics_by_invalid_id(self):
        """Test GET /api/v1/metrics/call/{id} with invalid ID"""
        try:
            invalid_id = "00000000-0000-0000-0000-000000000000"

            response = requests.get(
                f"{BASE_URL}/api/v1/metrics/call/{invalid_id}",
                headers=HEADERS,
                verify=False,
            )

            self.log_test(
                "GET /api/v1/metrics/call/{id} with invalid ID - Status Code",
                response.status_code == 404,
                f"Got {response.status_code}",
            )

            if response.status_code == 404:
                data = response.json()
                self.log_test(
                    "GET /api/v1/metrics/call/{id} with invalid ID - Error message",
                    "detail" in data and "not found" in data["detail"].lower(),
                )

        except Exception as e:
            self.log_test(
                "GET /api/v1/metrics/call/{id} with invalid ID - Request", False, str(e)
            )

    def test_get_metrics_summary(self):
        """Test GET /api/v1/metrics/call/summary"""
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/metrics/call/summary", headers=HEADERS, verify=False
            )

            self.log_test(
                "GET /api/v1/metrics/call/summary - Status Code",
                response.status_code == 200,
                f"Got {response.status_code}",
            )

            if response.status_code != 200:
                return

            data = response.json()

            # Test response structure
            required_fields = [
                "total_calls",
                "acceptance_rate",
                "average_final_rate",
                "response_distribution",
                "top_rejection_reasons",
                "period",
            ]
            for field in required_fields:
                self.log_test(
                    f"GET /api/v1/metrics/call/summary - Has {field} field",
                    field in data,
                    f"Missing field: {field}",
                )

            # Validate data types
            if "total_calls" in data:
                self.log_test(
                    "GET /api/v1/metrics/call/summary - Total calls is int",
                    isinstance(data["total_calls"], int),
                )

            if "acceptance_rate" in data:
                rate = data["acceptance_rate"]
                self.log_test(
                    "GET /api/v1/metrics/call/summary - Acceptance rate is valid",
                    isinstance(rate, (int, float)) and 0 <= rate <= 1,
                    f"Got {rate}",
                )

            if "response_distribution" in data:
                self.log_test(
                    "GET /api/v1/metrics/call/summary - Response distribution is dict",
                    isinstance(data["response_distribution"], dict),
                )

            # Validate calculation logic
            if (
                "response_distribution" in data
                and "acceptance_rate" in data
                and "total_calls" in data
            ):
                dist = data["response_distribution"]
                total_calls = data["total_calls"]
                acceptance_rate = data["acceptance_rate"]

                if total_calls > 0:
                    accepted_count = dist.get("ACCEPTED", 0)
                    calculated_rate = accepted_count / total_calls
                    rate_diff = abs(calculated_rate - acceptance_rate)

                    self.log_test(
                        "GET /api/v1/metrics/call/summary - Acceptance rate calculation",
                        rate_diff < 0.01,  # Allow small floating point differences
                        f"Expected {calculated_rate}, got {acceptance_rate}",
                    )

        except Exception as e:
            self.log_test("GET /api/v1/metrics/call/summary - Request", False, str(e))

    def test_authentication(self):
        """Test API key authentication"""
        try:
            # Test without API key
            response = requests.get(f"{BASE_URL}/api/v1/metrics/call", verify=False)
            self.log_test(
                "Authentication - No API key returns 401",
                response.status_code == 401,
                f"Got {response.status_code}",
            )

            # Test with invalid API key
            invalid_headers = {
                "X-API-Key": "invalid-key",
                "Content-Type": "application/json",
            }
            response = requests.get(
                f"{BASE_URL}/api/v1/metrics/call", headers=invalid_headers, verify=False
            )
            self.log_test(
                "Authentication - Invalid API key returns 401",
                response.status_code == 401,
                f"Got {response.status_code}",
            )

            # Test with valid API key (should work)
            response = requests.get(
                f"{BASE_URL}/api/v1/metrics/call", headers=HEADERS, verify=False
            )
            self.log_test(
                "Authentication - Valid API key returns 200",
                response.status_code == 200,
                f"Got {response.status_code}",
            )

        except Exception as e:
            self.log_test("Authentication - Test", False, str(e))

    def test_edge_cases(self):
        """Test edge cases and error conditions"""
        try:
            # Test with malformed UUID
            response = requests.get(
                f"{BASE_URL}/api/v1/metrics/call/not-a-uuid",
                headers=HEADERS,
                verify=False,
            )
            self.log_test(
                "Edge case - Malformed UUID returns error",
                response.status_code in [400, 422],
                f"Got {response.status_code}",
            )

            # Test with very large limit
            response = requests.get(
                f"{BASE_URL}/api/v1/metrics/call?limit=10000",
                headers=HEADERS,
                verify=False,
            )
            # Should either accept (with reasonable limit) or return 422 for validation error
            self.log_test(
                "Edge case - Large limit handled",
                response.status_code in [200, 422],
                f"Got {response.status_code}",
            )

            # Test with invalid date format
            response = requests.get(
                f"{BASE_URL}/api/v1/metrics/call?start_date=invalid-date",
                headers=HEADERS,
                verify=False,
            )
            self.log_test(
                "Edge case - Invalid date format returns error",
                response.status_code in [400, 422],
                f"Got {response.status_code}",
            )

            # Test with start_date > end_date
            response = requests.get(
                f"{BASE_URL}/api/v1/metrics/call?start_date=2025-08-22T00:00:00Z&end_date=2025-08-21T00:00:00Z",
                headers=HEADERS,
                verify=False,
            )
            # This might be handled gracefully or return an error
            self.log_test(
                "Edge case - Start date after end date handled",
                response.status_code in [200, 400],
                f"Got {response.status_code}",
            )

        except Exception as e:
            self.log_test("Edge cases - Test", False, str(e))

    def run_all_tests(self):
        """Run all test cases"""
        print("Starting HappyRobot Metrics API Endpoint Tests\n")

        self.test_get_all_metrics()
        print()

        self.test_get_metrics_with_date_filters()
        print()

        self.test_get_metrics_with_pagination()
        print()

        self.test_get_metrics_by_valid_id()
        print()

        self.test_get_metrics_by_invalid_id()
        print()

        self.test_get_metrics_summary()
        print()

        self.test_authentication()
        print()

        self.test_edge_cases()
        print()

        # Summary
        total_tests = self.passed + self.failed
        print("Test Results Summary:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {self.passed}")
        print(f"   Failed: {self.failed}")
        print(f"   Success Rate: {(self.passed/total_tests)*100:.1f}%")

        if self.failed > 0:
            print("\nFailed Tests:")
            for result in self.results:
                if result["result"] == "FAIL":
                    print(f"   - {result['test']}")
                    if result["details"]:
                        print(f"     {result['details']}")


if __name__ == "__main__":
    tester = MetricsEndpointTester()
    tester.run_all_tests()
