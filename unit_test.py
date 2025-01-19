import unittest
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional, Set
import math
from enum import Enum
import heapq
from collections import defaultdict
from lucidity import Location,Restaurant,RouteOptimizer,Order

# [Previous Location, Restaurant, Order, DeliveryState, and RouteOptimizer classes remain the same]
# ... [Previous implementation code here] ...


class TestRouteOptimizer(unittest.TestCase):
    """Test cases for the RouteOptimizer class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Common test locations
        self.driver_loc = Location("Driver", 12.9340, 77.6150)
        self.r1_loc = Location("R1", 12.9350, 77.6200)
        self.r2_loc = Location("R2", 12.9320, 77.6180)
        self.c1_loc = Location("C1", 12.9360, 77.6250)
        self.c2_loc = Location("C2", 12.9310, 77.6220)
        
        # Create restaurants
        self.r1 = Restaurant(self.r1_loc, prep_time=20)
        self.r2 = Restaurant(self.r2_loc, prep_time=15)
        
        # Initialize optimizer
        self.optimizer = RouteOptimizer(self.driver_loc)

    def test_haversine_distance(self):
        """Test distance calculation between two points."""
        # Test known distance
        distance = self.optimizer.haversine_distance(
            Location("A", 12.9340, 77.6150),
            Location("B", 12.9350, 77.6200)
        )
        self.assertGreater(distance, 0)
        
        # Test zero distance
        distance = self.optimizer.haversine_distance(
            Location("A", 12.9340, 77.6150),
            Location("A", 12.9340, 77.6150)
        )
        self.assertEqual(distance, 0)
        
        # Test symmetry
        dist1 = self.optimizer.haversine_distance(self.r1_loc, self.c1_loc)
        dist2 = self.optimizer.haversine_distance(self.c1_loc, self.r1_loc)
        self.assertAlmostEqual(dist1, dist2)

    def test_travel_time(self):
        """Test travel time calculations."""
        # Test with known locations
        time = self.optimizer.travel_time(self.r1_loc, self.c1_loc)
        self.assertGreater(time, 0)
        
        # Test zero distance travel
        time = self.optimizer.travel_time(self.r1_loc, self.r1_loc)
        self.assertEqual(time, 0)

    def test_single_order(self):
        """Test optimization with a single order."""
        orders = [Order("1", self.r1, self.c1_loc)]
        route, total_time, timeline = self.optimizer.optimize_route(orders)
        
        # Check route length
        self.assertEqual(len(route), 2)  # Should visit restaurant and customer
        
        # Check route validity
        self.assertEqual(route[0], self.r1_loc)  # Should visit restaurant first
        self.assertEqual(route[1], self.c1_loc)  # Then customer
        
        # Check timeline
        self.assertTrue(any(event['action'] == 'pickup' for event in timeline))
        self.assertTrue(any(event['action'] == 'delivery' for event in timeline))

    def test_multiple_orders(self):
        """Test optimization with multiple orders."""
        orders = [
            Order("1", self.r1, self.c1_loc),
            Order("2", self.r2, self.c2_loc)
        ]
        route, total_time, timeline = self.optimizer.optimize_route(orders)
        
        # Check route length
        self.assertEqual(len(route), 4)  # Should visit 2 restaurants and 2 customers
        
        # Check timeline completeness
        pickup_events = sum(1 for event in timeline if event['action'] == 'pickup')
        delivery_events = sum(1 for event in timeline if event['action'] == 'delivery')
        self.assertEqual(pickup_events, 2)
        self.assertEqual(delivery_events, 2)

    def test_preparation_time_handling(self):
        """Test handling of restaurant preparation times."""
        # Create order with long prep time
        long_prep_restaurant = Restaurant(self.r1_loc, prep_time=30)
        orders = [Order("1", long_prep_restaurant, self.c1_loc)]
        
        route, total_time, timeline = self.optimizer.optimize_route(orders)
        
        # Check for waiting events in timeline
        waiting_events = [event for event in timeline if event['action'] == 'waiting']
        self.assertTrue(len(waiting_events) > 0)
        
        # Verify waiting duration
        if waiting_events:
            wait_event = waiting_events[0]
            wait_duration = wait_event['end_time'] - wait_event['start_time']
            self.assertGreater(wait_duration, 0)

    def test_optimization_constraints(self):
        """Test that optimization maintains required constraints."""
        orders = [
            Order("1", self.r1, self.c1_loc),
            Order("2", self.r2, self.c2_loc)
        ]
        route, total_time, timeline = self.optimizer.optimize_route(orders)
        
        # Track order of operations
        pickup_times = {}
        delivery_times = {}
        
        for event in timeline:
            if event['action'] == 'pickup':
                pickup_times[event['order_id']] = event['time']
            elif event['action'] == 'delivery':
                delivery_times[event['order_id']] = event['time']
        
        # Verify pickup before delivery for each order
        for order_id in pickup_times:
            self.assertLess(
                pickup_times[order_id],
                delivery_times[order_id],
                f"Order {order_id} was delivered before pickup"
            )

    def test_timeline_continuity(self):
        """Test that the timeline is continuous and makes sense."""
        orders = [
            Order("1", self.r1, self.c1_loc),
            Order("2", self.r2, self.c2_loc)
        ]
        route, total_time, timeline = self.optimizer.optimize_route(orders)
        
        # Check time increases monotonically
        last_time = 0
        for event in timeline:
            if event['action'] == 'waiting':
                self.assertGreaterEqual(event['start_time'], last_time)
                self.assertGreater(event['end_time'], event['start_time'])
                last_time = event['end_time']
            else:
                self.assertGreaterEqual(event['time'], last_time)
                last_time = event['time']

def run_tests():
    """Run all test cases."""
    unittest.main()

if __name__ == "__main__":
    run_tests()
