import sys
from dotenv import load_dotenv

# Load env variables before importing any app modules that might depend on them
load_dotenv()

from app.core.database import SessionLocal
from app.core.graph_manager import GraphManager
from app.services.astar_service import AStarService
from app.schemas.route_schema import RoutePriority

def print_menu():
    print("\n" + "="*40)
    print("SUBWAY ROUTING - INTERACTIVE TEST")
    print("="*40)
    print("1. [Admin] Set Closures (Stations, Edges, Lines)")
    print("2. [Admin] View Current Closures")
    print("3. [User] Find Route (by Coordinates)")
    print("4. [Admin] Reload Graph Data")
    print("5. Exit")
    print("="*40)

def admin_set_closures():
    print("\n--- Enter closures (comma-separated, leave blank to skip) ---")
    stations_input = input("Stations to close: ").strip()
    edges_input = input("Edges to close (IDs): ").strip()
    lines_input = input("Lines to close: ").strip()
    
    stations = [s.strip() for s in stations_input.split(',')] if stations_input else []
    
    edges = []
    if edges_input:
        try:
            edges = [int(e.strip()) for e in edges_input.split(',')]
        except ValueError:
            print("Invalid input for edges. Must be integers.")
            
    lines = [l.strip() for l in lines_input.split(',')] if lines_input else []
    
    GraphManager().set_closed_nodes(stations=stations, edges=edges, lines=lines)
    print("\n✅ Closures updated successfully!")

def admin_view_closures():
    closures = GraphManager().get_closed_nodes()
    print("\n--- Current Closures ---")
    print(f"Closed Stations: {closures['closed_stations']}")
    print(f"Closed Edges (IDs): {closures['closed_edges']}")
    print(f"Closed Lines: {closures['closed_lines']}")

def user_find_route():
    print("\n--- Find Route ---")
    start_input = input("Start Station ID or Name: ").strip()
    end_input = input("End Station ID or Name: ").strip()
    
    gm = GraphManager()
    
    # helper to find station
    def resolve_station(query):
        if not query:
            return None
        # try ID first
        st = gm.get_station(query)
        if st:
            return st
        # try by exact or partial name
        for s in gm.stations.values():
            if query.lower() in s.name.lower():
                return s
        return None

    start_st = resolve_station(start_input)
    end_st = resolve_station(end_input)

    if not start_st:
        print(f"❌ Start station '{start_input}' not found.")
        return
    if not end_st:
        print(f"❌ End station '{end_input}' not found.")
        return

    print(f"\nRouting from: {start_st.name} ({start_st.id}) [Lat: {start_st.lat:.6f}, Lon: {start_st.lon:.6f}]")
    print(f"To: {end_st.name} ({end_st.id}) [Lat: {end_st.lat:.6f}, Lon: {end_st.lon:.6f}]")
    
    print("\nSelect Priority:")
    print("1. Shortest Distance")
    print("2. Lowest Fare")
    print("3. Fewest Transfers")
    p_choice = input("Choice (1/2/3) [default 1]: ").strip()
    
    priority = RoutePriority.SHORTEST_DISTANCE
    if p_choice == '2':
        priority = RoutePriority.LOWEST_FARE
    elif p_choice == '3':
        priority = RoutePriority.FEWEST_TRANSFERS

    print("\nSelect Passenger Type:")
    print("1. Adult")
    print("2. Child")
    pass_choice = input("Choice (1/2) [default 1]: ").strip()
    passenger_type = "child" if pass_choice == '2' else "adult"

    astar = AStarService()
    result = astar.find_route(
        start_coords=(start_st.lat, start_st.lon),
        end_coords=(end_st.lat, end_st.lon),
        priority=priority
    )
    
    if not result:
        print("\n❌ No route found between the specified coordinates under the given constraints.")
        return
        
    path, total_distance = result
    
    # Import velocity config inside to calculate time
    from app.core.config import AVERAGE_VELOCITY
    from app.services.astar_service import calculate_fare
    
    estimated_time = (total_distance / AVERAGE_VELOCITY) * 60.0
    total_fare = calculate_fare(total_distance, passenger_type)
    
    path_names = []
    for st_id in path:
        name = gm.get_station(st_id).name if gm.get_station(st_id) else st_id
        if not path_names or path_names[-1] != name:
            path_names.append(name)
    
    print("\n--- Route Result ---")
    print(f"Path: {' -> '.join(path_names)}")
    print(f"Total Subway Distance: {total_distance:.2f} km")
    print(f"Total Estimated Time: {estimated_time:.1f} minutes")
    print(f"Total Fare: ¥{total_fare} ({passenger_type.capitalize()})")

def reload_graph():
    print("\nLoading Graph Data from Database...")
    db = SessionLocal()
    try:
        GraphManager().reload_graph(db)
        print("✅ Graph data loaded successfully.")
    except Exception as e:
        print(f"❌ Failed to load graph: {e}")
    finally:
        db.close()

def main():
    # Initial load
    reload_graph()
    
    while True:
        print_menu()
        choice = input("Select an option: ").strip()
        
        if choice == '1':
            admin_set_closures()
        elif choice == '2':
            admin_view_closures()
        elif choice == '3':
            user_find_route()
        elif choice == '4':
            reload_graph()
        elif choice == '5':
            print("Exiting...")
            sys.exit(0)
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main()
