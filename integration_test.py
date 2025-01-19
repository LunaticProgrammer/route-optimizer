import unittest
import json
import time
from dataclasses import dataclass, asdict
from typing import List, Tuple, Dict, Optional, Set
import math
from enum import Enum
import heapq
from collections import defaultdict
import logging
from datetime import datetime
from lucidity import Location,Order,RouteOptimizer,Restaurant

# [Previous classes and unit tests remain the same]
# ... [Previous implementation code here] ...

class IntegrationTests(unittest.TestCase):
    """Integration tests for the complete delivery workflow."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all integration tests."""
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            filename=f'integration_tests_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        )
        cls.logger = logging.getLogger(__name__)

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.logger.info("Starting new integration test")
        
        # Create a realistic delivery scenario in Koramangala
        self.driver_loc = Location("Driver", 12.9340, 77.6150)  # Starting point
        
        # Multiple restaurants in different areas
        self.restaurants = {
            "restaurant_1": Restaurant(
                Location("Empire Restaurant", 12.9350, 77.6200),
                prep_time=20
            ),
            "restaurant_2": Restaurant(
                Location("Meghana Foods", 12.9320, 77.6180),
                prep_time=15
            ),
            "restaurant_3": Restaurant(
                Location("Biriyani Zone", 12.9310, 77.6190),
                prep_time=25
            )
        }
        
        # Multiple delivery locations
        self.customers = {
            "customer_1": Location("Customer 1", 12.9360, 77.6250),
            "customer_2": Location("Customer 2", 12.9310, 77.6220),
            "customer_3": Location("Customer 3", 12.9330, 77.6210)
        }
        
        self.optimizer = RouteOptimizer(self.driver_loc)

    def test_full_delivery_workflow(self):
        """Test complete delivery workflow with multiple orders."""
        self.logger.info("Testing full delivery workflow")
        
        # Create multiple orders
        orders = [
            Order("1", self.restaurants["restaurant_1"], self.customers["customer_1"]),
            Order("2", self.restaurants["restaurant_2"], self.customers["customer_2"]),
            Order("3", self.restaurants["restaurant_3"], self.customers["customer_3"])
        ]
        
        # Get optimized route
        route, total_time, timeline = self.optimizer.optimize_route(orders)
        
        # Verify complete workflow
        self.verify_workflow(orders, route, timeline)
        
        self.logger.info(f"Full workflow test completed. Total time: {total_time:.2f} minutes")

    def verify_workflow(self, orders: List[Order], route: List[Location], timeline: List[dict]):
        """Verify the entire workflow meets all business requirements."""
        # Track order states
        order_states = {order.id: {
            'pickup_time': None,
            'delivery_time': None,
            'wait_start': None,
            'wait_end': None
        } for order in orders}
        
        # Analyze timeline
        for event in timeline:
            order_id = event['order_id']
            if event['action'] == 'waiting':
                order_states[order_id]['wait_start'] = event['start_time']
                order_states[order_id]['wait_end'] = event['end_time']
            elif event['action'] == 'pickup':
                order_states[order_id]['pickup_time'] = event['time']
            elif event['action'] == 'delivery':
                order_states[order_id]['delivery_time'] = event['time']
        
        # Verify each order's workflow
        for order in orders:
            state = order_states[order.id]
            
            # Verify order completion
            self.assertIsNotNone(state['pickup_time'], f"Order {order.id} was never picked up")
            self.assertIsNotNone(state['delivery_time'], f"Order {order.id} was never delivered")
            
            # Verify order sequence
            self.assertLess(state['pickup_time'], state['delivery_time'],
                          f"Order {order.id} was delivered before pickup")
            
            # Verify preparation time handling
            if state['wait_start'] is not None:
                wait_duration = state['wait_end'] - state['wait_start']
                self.assertGreaterEqual(wait_duration, 0,
                                      f"Invalid waiting time for order {order.id}")

    def test_concurrent_orders_handling(self):
        """Test handling of concurrent orders with overlapping preparation times."""
        self.logger.info("Testing concurrent orders handling")
        
        # Create orders with overlapping prep times
        orders = [
            Order("1", 
                 Restaurant(self.restaurants["restaurant_1"].location, prep_time=20),
                 self.customers["customer_1"]),
            Order("2", 
                 Restaurant(self.restaurants["restaurant_2"].location, prep_time=20),
                 self.customers["customer_2"])
        ]
        
        route, total_time, timeline = self.optimizer.optimize_route(orders)
        
        # Verify efficient handling of concurrent preparation
        self.analyze_concurrent_efficiency(timeline)
        
        self.logger.info(f"Concurrent orders test completed. Total time: {total_time:.2f} minutes")

    def analyze_concurrent_efficiency(self, timeline: List[dict]):
        """Analyze how efficiently concurrent orders are handled."""
        waiting_periods = []
        active_periods = []
        
        for event in timeline:
            if event['action'] == 'waiting':
                waiting_periods.append((event['start_time'], event['end_time']))
            else:
                active_periods.append(event['time'])
        
        # Check for overlapping waiting periods
        if len(waiting_periods) > 1:
            for i in range(len(waiting_periods) - 1):
                self.assertFalse(
                    waiting_periods[i][1] > waiting_periods[i+1][0],
                    "Inefficient handling of concurrent orders detected"
                )
    def test_performance_consistency(self):
        """Test consistency of optimization results."""
        self.logger.info("Testing performance consistency")
        
        # Create test orders
        orders = [
            Order("1", self.restaurants["restaurant_1"], self.customers["customer_1"]),
            Order("2", self.restaurants["restaurant_2"], self.customers["customer_2"])
        ]
        
        # Run multiple optimizations
        results = []
        for _ in range(5):
            route, total_time, timeline = self.optimizer.optimize_route(orders)
            results.append(total_time)
            
        # Check consistency
        avg_time = sum(results) / len(results)
        for time in results:
            # Allow 5% variation
            self.assertLess(abs(time - avg_time) / avg_time, 0.05,
                          "Inconsistent optimization results detected")
        
        self.logger.info(f"Consistency test completed. Average time: {avg_time:.2f} minutes")

    def test_state_transitions(self):
        """Test correct state transitions throughout the delivery process."""
        self.logger.info("Testing state transitions")
        
        orders = [
            Order("1", self.restaurants["restaurant_1"], self.customers["customer_1"]),
            Order("2", self.restaurants["restaurant_2"], self.customers["customer_2"])
        ]
        
        route, total_time, timeline = self.optimizer.optimize_route(orders)
        
        # Verify state transitions
        current_state = {'picked_up': set(), 'delivered': set()}
        last_time = 0
        
        for event in timeline:
            # Time should always move forward
            if event['action'] != 'waiting':
                self.assertGreater(event['time'], last_time)
                last_time = event['time']
            
            # Verify state transitions
            if event['action'] == 'pickup':
                self.assertNotIn(event['order_id'], current_state['picked_up'])
                current_state['picked_up'].add(event['order_id'])
            elif event['action'] == 'delivery':
                self.assertIn(event['order_id'], current_state['picked_up'])
                self.assertNotIn(event['order_id'], current_state['delivered'])
                current_state['delivered'].add(event['order_id'])
        
        self.logger.info("State transition test completed successfully")

def run_integration_tests():
    """Run all integration tests."""
    suite = unittest.TestLoader().loadTestsFromTestCase(IntegrationTests)
    unittest.TextTestRunner(verbosity=2).run(suite)

if __name__ == "__main__":
    run_integration_tests()
