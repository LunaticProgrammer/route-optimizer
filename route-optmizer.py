from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional, Set
import math
from enum import Enum
import heapq
from collections import defaultdict

@dataclass
class Location:
    """Represents a geographical location with latitude and longitude."""
    name: str
    lat: float
    lon: float

@dataclass
class Restaurant:
    """Represents a restaurant with its location and preparation time."""
    location: Location
    prep_time: float  # in minutes

@dataclass
class Order:
    """Represents a delivery order with restaurant and customer details."""
    id: str
    restaurant: Restaurant
    customer: Location
    
class DeliveryState:
    """Represents the current state of deliveries and time calculations."""
    def __init__(self, current_location: Location, current_time: float):
        self.location = current_location
        self.time = current_time
        self.picked_up_orders: Set[str] = set()
        self.delivered_orders: Set[str] = set()
        self.restaurant_arrival_times: Dict[str, float] = {}

class RouteOptimizer:
    """Optimizes delivery routes using nearest neighbor approach with preparation time considerations."""
    
    EARTH_RADIUS = 6371  # Earth's radius in kilometers
    AVG_SPEED = 20  # Average speed in km/hr
    
    def __init__(self, driver_location: Location):
        """Initialize the route optimizer."""
        self.driver_location = driver_location
        
    def haversine_distance(self, loc1: Location, loc2: Location) -> float:
        """Calculate the great circle distance between two points on Earth."""
        lat1, lon1 = math.radians(loc1.lat), math.radians(loc1.lon)
        lat2, lon2 = math.radians(loc2.lat), math.radians(loc2.lon)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return self.EARTH_RADIUS * c
    
    def travel_time(self, loc1: Location, loc2: Location) -> float:
        """Calculate travel time between two locations in minutes."""
        distance = self.haversine_distance(loc1, loc2)
        return (distance / self.AVG_SPEED) * 60
    
    def find_nearest_valid_location(self, 
                                  state: DeliveryState, 
                                  orders: List[Order],
                                  waiting_required: bool = False) -> Tuple[Optional[Location], Optional[str], float]:
        """
        Find the nearest valid next location considering preparation times.
        
        Args:
            state: Current delivery state
            orders: List of all orders
            waiting_required: Whether to consider locations where waiting is required
            
        Returns:
            Tuple of (next location, order ID, arrival time)
        """
        best_location = None
        best_order_id = None
        best_arrival_time = float('inf')
        
        for order in orders:
            # Check restaurant pickup
            if (order.id not in state.picked_up_orders and 
                (not waiting_required or 
                 state.time + self.travel_time(state.location, order.restaurant.location) < order.restaurant.prep_time)):
                
                arrival_time = state.time + self.travel_time(state.location, order.restaurant.location)
                if arrival_time < best_arrival_time:
                    best_location = order.restaurant.location
                    best_order_id = order.id
                    best_arrival_time = arrival_time
                    
            # Check customer delivery
            if (order.id in state.picked_up_orders and 
                order.id not in state.delivered_orders):
                
                arrival_time = state.time + self.travel_time(state.location, order.customer)
                if arrival_time < best_arrival_time:
                    best_location = order.customer
                    best_order_id = order.id
                    best_arrival_time = arrival_time
                    
        return best_location, best_order_id, best_arrival_time
    
    def optimize_route(self, orders: List[Order]) -> Tuple[List[Location], float, List[dict]]:
        """
        Find optimal route using nearest neighbor approach with preparation time considerations.
        
        Returns:
            Tuple of (route locations, total time, detailed timeline)
        """
        state = DeliveryState(self.driver_location, 0)
        route = []
        timeline = []
        
        while len(state.delivered_orders) < len(orders):
            # Try to find nearest location without waiting
            next_loc, order_id, arrival_time = self.find_nearest_valid_location(state, orders)
            
            # If no location found, look for locations where waiting is required
            if not next_loc:
                next_loc, order_id, arrival_time = self.find_nearest_valid_location(state, orders, waiting_required=True)
            
            # Update state and route
            if next_loc:
                # Travel to location
                state.time = arrival_time
                
                # Handle restaurant arrival
                matching_order = next(o for o in orders if o.id == order_id)
                if next_loc == matching_order.restaurant.location:
                    # Wait for preparation if needed
                    prep_end_time = max(state.time, matching_order.restaurant.prep_time)
                    if prep_end_time > state.time:
                        timeline.append({
                            'action': 'waiting',
                            'location': next_loc.name,
                            'order_id': order_id,
                            'start_time': state.time,
                            'end_time': prep_end_time
                        })
                        state.time = prep_end_time
                    
                    state.picked_up_orders.add(order_id)
                    timeline.append({
                        'action': 'pickup',
                        'location': next_loc.name,
                        'order_id': order_id,
                        'time': state.time
                    })
                else:
                    # Handle customer delivery
                    state.delivered_orders.add(order_id)
                    timeline.append({
                        'action': 'delivery',
                        'location': next_loc.name,
                        'order_id': order_id,
                        'time': state.time
                    })
                
                route.append(next_loc)
                state.location = next_loc
            
        return route, state.time, timeline

def main():
    """Example usage of the optimized RouteOptimizer."""
    # Example coordinates (replace with actual coordinates)
    driver = Location("Aman", 12.9340, 77.6150)  # Koramangala coordinates
    
    r1 = Restaurant(
        Location("R1", 12.9350, 77.6200),
        prep_time=20  # 20 minutes preparation time
    )
    
    r2 = Restaurant(
        Location("R2", 12.9320, 77.6180),
        prep_time=15  # 15 minutes preparation time
    )
    
    c1 = Location("C1", 12.9360, 77.6250)
    c2 = Location("C2", 12.9310, 77.6220)
    
    orders = [
        Order("1", r1, c1),
        Order("2", r2, c2)
    ]
    
    optimizer = RouteOptimizer(driver)
    route, total_time, timeline = optimizer.optimize_route(orders)
    
    print("Optimized Route Timeline:")
    for event in timeline:
        if event['action'] == 'waiting':
            print(f"Waiting at {event['location']} for order {event['order_id']}")
            print(f"  From {event['start_time']:.1f} to {event['end_time']:.1f} minutes")
        else:
            print(f"{event['action'].title()} at {event['location']} for order {event['order_id']}")
            print(f"  Time: {event['time']:.1f} minutes")
    
    print(f"\nTotal delivery time: {total_time:.1f} minutes")

if __name__ == "__main__":
    main()
