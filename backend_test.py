#!/usr/bin/env python3

import requests
import sys
import time
import json
import uuid
from datetime import datetime

class CalmTailsAPITester:
    def __init__(self, base_url="https://calmtails-staging.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.admin_token = None
        self.user_id = None
        self.cart_session_id = f"test_cart_{int(time.time())}"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
    def log_test_result(self, test_name, passed, response_time, status_code, message=""):
        """Log test result for analysis"""
        result = {
            "test_name": test_name,
            "passed": passed,
            "response_time": response_time,
            "status_code": status_code,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            print(f"✅ {test_name} - {response_time:.2f}s - {message}")
        else:
            print(f"❌ {test_name} - {response_time:.2f}s - Status {status_code} - {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test with timing"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('/') else f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Use admin token for admin endpoints, otherwise use regular token
        if endpoint.startswith('admin/') and self.admin_token:
            headers['Authorization'] = f'Bearer {self.admin_token}'
        elif self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        print(f"\n🔍 Testing {name}...")
        start_time = time.time()
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers, timeout=timeout)

            response_time = time.time() - start_time
            
            success = response.status_code == expected_status
            
            # Try to get JSON response
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text[:200]}
                
            message = f"Response preview: {str(response_data)[:100]}..."
            self.log_test_result(name, success, response_time, response.status_code, message)
            
            return success, response_data, response_time

        except requests.exceptions.Timeout:
            response_time = time.time() - start_time
            self.log_test_result(name, False, response_time, 0, "Request timeout")
            return False, {}, response_time
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test_result(name, False, response_time, 0, f"Error: {str(e)}")
            return False, {}, response_time

    def test_health_check(self):
        """Test basic health endpoints"""
        print("\n=== HEALTH CHECK TESTS ===")
        self.run_test("API Root", "GET", "", 200)
        self.run_test("Health Check", "GET", "health", 200)

    def test_seed_products(self):
        """Test seeding products database"""
        print("\n=== SEED PRODUCTS TEST ===")
        
        success, response, response_time = self.run_test(
            "Seed Products", 
            "POST", 
            "seed-products", 
            200,
            timeout=60
        )
        
        if success:
            print(f"   ✅ Products seeded successfully")
            return True
        else:
            print(f"   ❌ Failed to seed products - {response}")
            return False

    def test_products_api(self):
        """Test products endpoints"""
        print("\n=== PRODUCTS API TESTS ===")
        
        # Test get all products
        success, response, _ = self.run_test(
            "Get All Products",
            "GET",
            "products",
            200
        )
        
        product_count = len(response) if isinstance(response, list) else 0
        print(f"   📦 Found {product_count} products")
        
        # Test featured products
        success, response, _ = self.run_test(
            "Get Featured Products",
            "GET",
            "products/featured",
            200
        )
        
        featured_count = len(response) if isinstance(response, list) else 0
        print(f"   ⭐ Found {featured_count} featured products")
        
        # Test categories
        success, response, _ = self.run_test(
            "Get Categories",
            "GET",
            "products/categories",
            200
        )
        
        category_count = len(response) if isinstance(response, list) else 0
        print(f"   📂 Found {category_count} categories")
        
        # Test product filters
        self.run_test(
            "Filter Products by Pet Type (dogs)",
            "GET",
            "products?pet_type=dog",
            200
        )
        
        self.run_test(
            "Filter Products by Pet Type (cats)", 
            "GET",
            "products?pet_type=cat",
            200
        )
        
        # Test individual product by slug
        if product_count > 0:
            # Get first product to test slug endpoint
            success, products, _ = self.run_test(
                "Get Products for Slug Test",
                "GET", 
                "products",
                200
            )
            
            if success and products and len(products) > 0:
                first_product = products[0]
                slug = first_product.get('slug')
                if slug:
                    self.run_test(
                        f"Get Product by Slug ({slug})",
                        "GET",
                        f"products/{slug}",
                        200
                    )
                    return first_product
        
        return None

    def test_user_registration(self):
        """Test user registration with discount code"""
        print("\n=== USER REGISTRATION TEST ===")
        
        timestamp = int(time.time())
        test_email = f"test_user_{timestamp}@calmtails.com"
        
        user_data = {
            "email": test_email,
            "password": "TestPass123!",
            "name": f"Test User {timestamp}"
        }
        
        success, response, _ = self.run_test(
            "User Registration", 
            "POST", 
            "auth/register", 
            200, 
            user_data,
            timeout=60
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response.get('user', {}).get('id')
            discount_code = response.get('user', {}).get('discount_code')
            
            print(f"   📝 Registration successful!")
            print(f"   🎫 Discount code: {discount_code}")
            print(f"   👤 User ID: {self.user_id}")
            return True
        else:
            print(f"   ❌ Registration failed - {response}")
            return False

    def test_admin_login(self):
        """Test admin login"""
        print("\n=== ADMIN LOGIN TEST ===")
        
        login_data = {
            "email": "admin@calmtails.com",
            "password": "admin123"
        }
        
        success, response, _ = self.run_test(
            "Admin Login",
            "POST",
            "auth/login", 
            200,
            login_data,
            timeout=30
        )
        
        if success and 'token' in response:
            self.admin_token = response['token']
            user = response.get('user', {})
            is_admin = user.get('is_admin', False)
            
            print(f"   📝 Admin login successful!")
            print(f"   👤 User: {user.get('name')}")
            print(f"   🔑 Is Admin: {is_admin}")
            return is_admin
        else:
            print(f"   ❌ Admin login failed - {response}")
            return False

    def test_cart_functionality(self, product):
        """Test cart operations"""
        print("\n=== CART FUNCTIONALITY TESTS ===")
        
        if not product:
            print("   ❌ No product available for cart testing")
            return False
        
        product_id = product.get('id')
        print(f"   🛒 Testing cart with product: {product.get('name', 'Unknown')}")
        
        # Get empty cart
        success, response, _ = self.run_test(
            "Get Empty Cart",
            "GET",
            f"cart/{self.cart_session_id}",
            200
        )
        
        # Add product to cart
        cart_item = {
            "product_id": product_id,
            "quantity": 2
        }
        
        success, response, _ = self.run_test(
            "Add Product to Cart",
            "POST",
            f"cart/{self.cart_session_id}/add",
            200,
            cart_item
        )
        
        if success:
            items = response.get('items', [])
            subtotal = response.get('subtotal', 0)
            print(f"   ✅ Cart now has {len(items)} items, subtotal: ${subtotal}")
        
        # Update quantity
        update_item = {
            "product_id": product_id,
            "quantity": 3
        }
        
        self.run_test(
            "Update Cart Item Quantity",
            "POST",
            f"cart/{self.cart_session_id}/update",
            200,
            update_item
        )
        
        # Remove item
        self.run_test(
            "Remove Item from Cart",
            "DELETE",
            f"cart/{self.cart_session_id}/item/{product_id}",
            200
        )
        
        # Add back for checkout test
        self.run_test(
            "Re-add Product for Checkout Test",
            "POST",
            f"cart/{self.cart_session_id}/add",
            200,
            cart_item
        )
        
        return True

    def test_checkout_flow(self):
        """Test checkout and Stripe integration"""
        print("\n=== CHECKOUT FLOW TEST ===")
        
        checkout_data = {
            "cart_session_id": self.cart_session_id,
            "email": "test@calmtails.com",
            "origin_url": self.base_url
        }
        
        success, response, _ = self.run_test(
            "Create Checkout Session",
            "POST",
            "checkout",
            200,
            checkout_data,
            timeout=60
        )
        
        if success and 'checkout_url' in response:
            checkout_url = response['checkout_url']
            session_id = response.get('session_id')
            order_id = response.get('order_id')
            
            print(f"   ✅ Checkout session created!")
            print(f"   🔗 Checkout URL: {checkout_url[:50]}...")
            print(f"   📋 Order ID: {order_id}")
            
            # Test checkout status
            if session_id:
                self.run_test(
                    "Get Checkout Status",
                    "GET",
                    f"checkout/status/{session_id}",
                    200
                )
            
            return order_id
        else:
            print(f"   ❌ Checkout failed - {response}")
            return None

    def test_orders_api(self):
        """Test order endpoints"""
        print("\n=== ORDERS API TEST ===")
        
        # Test get user orders (requires auth)
        if self.token:
            self.run_test(
                "Get User Orders",
                "GET",
                "orders",
                200
            )

    def test_admin_endpoints(self):
        """Test admin-specific endpoints"""
        print("\n=== ADMIN ENDPOINTS TEST ===")
        
        if not self.admin_token:
            print("   ❌ No admin token available")
            return False
        
        # Test admin stats
        success, response, _ = self.run_test(
            "Get Admin Stats",
            "GET",
            "admin/stats",
            200
        )
        
        if success:
            stats = response
            print(f"   📊 Total Orders: {stats.get('total_orders', 0)}")
            print(f"   💰 Total Revenue: ${stats.get('total_revenue', 0)}")
            print(f"   📦 Total Products: {stats.get('total_products', 0)}")
            print(f"   👥 Total Customers: {stats.get('total_customers', 0)}")
        
        # Test admin orders
        self.run_test(
            "Get All Orders (Admin)",
            "GET",
            "admin/orders",
            200
        )
        
        return True

    def test_agents_api(self):
        """Test AI agents endpoints"""
        print("\n=== AI AGENTS API TEST ===")
        
        # Test get agents list
        success, response, _ = self.run_test(
            "Get Agents List",
            "GET",
            "agents",
            200
        )
        
        if success and 'agents' in response:
            agents = response['agents']
            agent_count = len(agents)
            print(f"   🤖 Found {agent_count} agents")
            
            # Test agent chat (requires auth)
            if self.token and agent_count > 0:
                agent_type = list(agents.keys())[0] if agents else "product_sourcing"
                
                chat_data = {
                    "query": "Help me find calming products for anxious dogs",
                    "agent_type": agent_type,
                    "session_id": str(uuid.uuid4())
                }
                
                print(f"   🤖 Testing agent chat with {agent_type} (may take 30-60 seconds)...")
                success, response, _ = self.run_test(
                    f"Agent Chat - {agent_type}",
                    "POST",
                    "agents/chat",
                    200,
                    chat_data,
                    timeout=90
                )
                
                if success and 'response' in response:
                    ai_response = response['response']
                    print(f"   ✅ Agent responded ({len(ai_response)} chars)")
        
        return True

    def test_protected_routes(self):
        """Test authentication on protected routes"""
        print("\n=== PROTECTED ROUTES TEST ===")
        
        if not self.token:
            print("   ❌ No user token available")
            return False
        
        success, response, _ = self.run_test(
            "Get Current User (/auth/me)",
            "GET",
            "auth/me",
            200
        )
        
        if success:
            print(f"   ✅ Protected route working - User: {response.get('name')}")
            return True
        return False

    def save_test_results(self):
        """Save detailed test results to file"""
        results = {
            "test_run_summary": {
                "total_tests": self.tests_run,
                "passed_tests": self.tests_passed,
                "success_rate": f"{(self.tests_passed/self.tests_run*100):.1f}%",
                "timestamp": datetime.now().isoformat()
            },
            "detailed_results": self.test_results
        }
        
        with open('/app/test_results_backend.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📋 Detailed test results saved to: /app/test_results_backend.json")

def main():
    print("🚀 Starting CalmTails E-commerce API Tests")
    print("=" * 60)
    
    tester = CalmTailsAPITester()
    
    # Run test suite
    tests_passed = []
    
    # Health checks
    tester.test_health_check()
    
    # Seed products first
    if tester.test_seed_products():
        tests_passed.append("seed_products")
    
    # Test products API
    product = tester.test_products_api()
    if product:
        tests_passed.append("products_api")
    
    # Test user registration
    if tester.test_user_registration():
        tests_passed.append("user_registration")
        
        # Test protected routes
        if tester.test_protected_routes():
            tests_passed.append("protected_routes")
        
        # Test cart functionality
        if tester.test_cart_functionality(product):
            tests_passed.append("cart_functionality")
            
            # Test checkout
            order_id = tester.test_checkout_flow()
            if order_id:
                tests_passed.append("checkout_flow")
        
        # Test orders API
        tester.test_orders_api()
        tests_passed.append("orders_api")
    
    # Test admin login and admin endpoints
    if tester.test_admin_login():
        tests_passed.append("admin_login")
        
        if tester.test_admin_endpoints():
            tests_passed.append("admin_endpoints")
    
    # Test AI agents
    if tester.test_agents_api():
        tests_passed.append("agents_api")
    
    # Save detailed results
    tester.save_test_results()
    
    # Final summary
    print("\n" + "=" * 60)
    print(f"🏁 FINAL RESULTS")
    print(f"📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"📈 Success rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    print(f"✅ Working features: {', '.join(tests_passed)}")
    
    if tester.tests_passed < tester.tests_run:
        print(f"❌ {tester.tests_run - tester.tests_passed} tests failed - check logs above")
        return 1
    else:
        print("🎉 All tests passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())