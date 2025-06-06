import os
import json
from datetime import datetime, timezone
from utils.config import BASE_DIR

class NavigationLogger:
    def __init__(self):
        self.logs_dir = os.path.join(BASE_DIR, 'logs', 'navigation')
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir, mode=0o775, exist_ok=True)
    
    def get_user_log_path(self, user_id):
        """Get the log file path for a specific user"""
        filename = f"navigation_{user_id}.json"
        return os.path.join(self.logs_dir, filename)
    
    def init_user_session(self, user_id, user_metadata):
        """Initialize a new navigation session for a user"""
        log_path = self.get_user_log_path(user_id)
        current_time = datetime.now(timezone.utc).isoformat()
        
        # Load existing log or create new one
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                log_data = json.load(f)
        else:
            log_data = {
                "user_id": user_id,
                "sessions": []
            }
        
        # Start new session
        new_session = {
            "session_id": f"session_{len(log_data['sessions']) + 1}_{current_time}",
            "session_start": current_time,
            "session_end": None,
            "total_session_duration": 0,
            "user_metadata": user_metadata,
            "navigation_sequence": [],
            "page_summary": {
                "pages_visited": [],
                "unique_pages": 0,
                "total_page_views": 0,
                "most_visited_page": None,
                "entry_page": None,
                "exit_page": None,
                "bounce_rate": False,
                "conversion_funnel": {}
            },
            "interaction_summary": {
                "total_clicks": 0,
                "total_scrolls": 0,
                "total_link_clicks": 0,
                "average_time_per_page": 0,
                "click_heatmap": [],
                "link_click_summary": []
            },
            "traversal_graph": {
                "nodes": [],
                "edges": [],
                "paths": []
            }
        }
        
        log_data["sessions"].append(new_session)
        
        # Save updated log
        with open(log_path, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        return new_session["session_id"]
    
    def log_page_visit(self, user_id, page_data):
        """Log a page visit"""
        log_path = self.get_user_log_path(user_id)
        
        if not os.path.exists(log_path):
            return False
        
        try:
            with open(log_path, 'r') as f:
                log_data = json.load(f)
            
            # Get current session (last one)
            if not log_data["sessions"]:
                return False
            
            current_session = log_data["sessions"][-1]
            
            # Add page visit to navigation sequence
            sequence_id = len(current_session["navigation_sequence"]) + 1
            page_visit = {
                "sequence_id": sequence_id,
                "page": page_data.get("page"),
                "url": page_data.get("url"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "entry_method": page_data.get("entry_method", "direct"),
                "time_on_page": 0,  # Will be updated when leaving page
                "scroll_depth": 0,
                "interactions": []
            }
            
            # Update previous page's time_on_page if exists
            if current_session["navigation_sequence"]:
                prev_page = current_session["navigation_sequence"][-1]
                prev_timestamp = datetime.fromisoformat(prev_page["timestamp"].replace('Z', '+00:00'))
                current_timestamp = datetime.fromisoformat(page_visit["timestamp"].replace('Z', '+00:00'))
                time_diff = (current_timestamp - prev_timestamp).total_seconds()
                prev_page["time_on_page"] = time_diff
            
            current_session["navigation_sequence"].append(page_visit)
            
            # Update page summary
            page_name = page_data.get("page")
            if page_name not in current_session["page_summary"]["pages_visited"]:
                current_session["page_summary"]["pages_visited"].append(page_name)
            
            current_session["page_summary"]["total_page_views"] += 1
            current_session["page_summary"]["unique_pages"] = len(current_session["page_summary"]["pages_visited"])
            
            if sequence_id == 1:
                current_session["page_summary"]["entry_page"] = page_name
            
            current_session["page_summary"]["exit_page"] = page_name
            
            # Save updated log
            with open(log_path, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error logging page visit: {str(e)}")
            return False
    
    def log_interaction(self, user_id, interaction_data):
        """Log user interaction (click, scroll, link click, etc.)"""
        log_path = self.get_user_log_path(user_id)
        
        if not os.path.exists(log_path):
            return False
        
        try:
            with open(log_path, 'r') as f:
                log_data = json.load(f)
            
            # Get current session and current page
            if not log_data["sessions"] or not log_data["sessions"][-1]["navigation_sequence"]:
                return False
            
            current_session = log_data["sessions"][-1]
            current_page = current_session["navigation_sequence"][-1]
            
            # Add interaction to current page
            interaction = {
                "type": interaction_data.get("type"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "element_type": interaction_data.get("element_type"),
                "element_id": interaction_data.get("element_id"),
                "element_class": interaction_data.get("element_class"),
                "coordinates": interaction_data.get("coordinates", {}),
                "scroll_position": interaction_data.get("scroll_position", 0)
            }
            
            # Add link-specific data if it's a link click
            if interaction_data.get("type") == "link_click":
                interaction.update({
                    "link_text": interaction_data.get("link_text"),
                    "link_href": interaction_data.get("link_href"),
                    "link_target": interaction_data.get("link_target", "_self"),
                    "is_external": interaction_data.get("is_external", False)
                })
                current_session["interaction_summary"]["total_link_clicks"] += 1
                
                # Update link click summary
                link_summary = {
                    "link_text": interaction_data.get("link_text"),
                    "link_href": interaction_data.get("link_href"),
                    "count": 1
                }
                
                # Check if link already exists in summary
                existing_link = None
                for link in current_session["interaction_summary"]["link_click_summary"]:
                    if link["link_href"] == interaction_data.get("link_href"):
                        existing_link = link
                        break
                
                if existing_link:
                    existing_link["count"] += 1
                else:
                    current_session["interaction_summary"]["link_click_summary"].append(link_summary)
            
            current_page["interactions"].append(interaction)
            
            # Update interaction summary
            if interaction_data.get("type") == "click":
                current_session["interaction_summary"]["total_clicks"] += 1
            elif interaction_data.get("type") == "scroll":
                current_session["interaction_summary"]["total_scrolls"] += 1
                current_page["scroll_depth"] = max(
                    current_page["scroll_depth"], 
                    interaction_data.get("scroll_depth", 0)
                )
            
            # Save updated log
            with open(log_path, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error logging interaction: {str(e)}")
            return False
    
    def end_session(self, user_id):
        """End the current navigation session and calculate summary statistics"""
        log_path = self.get_user_log_path(user_id)
        
        if not os.path.exists(log_path):
            return False
        
        try:
            with open(log_path, 'r') as f:
                log_data = json.load(f)
            
            if not log_data["sessions"]:
                return False
            
            current_session = log_data["sessions"][-1]
            current_time = datetime.now(timezone.utc).isoformat()
            
            # Update session end time
            current_session["session_end"] = current_time
            
            # Calculate total session duration
            start_time = datetime.fromisoformat(current_session["session_start"].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(current_time.replace('Z', '+00:00'))
            current_session["total_session_duration"] = (end_time - start_time).total_seconds()
            
            # Update last page's time_on_page
            if current_session["navigation_sequence"]:
                last_page = current_session["navigation_sequence"][-1]
                last_timestamp = datetime.fromisoformat(last_page["timestamp"].replace('Z', '+00:00'))
                time_diff = (end_time - last_timestamp).total_seconds()
                last_page["time_on_page"] = time_diff
            
            # Calculate summary statistics
            self._calculate_session_summary(current_session)
            
            # Save updated log
            with open(log_path, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error ending session: {str(e)}")
            return False
    
    def _calculate_session_summary(self, session):
        """Calculate summary statistics for a session"""
        navigation = session["navigation_sequence"]
        
        if not navigation:
            return
        
        # Calculate average time per page
        total_time = sum(page.get("time_on_page", 0) for page in navigation)
        session["interaction_summary"]["average_time_per_page"] = total_time / len(navigation) if navigation else 0
        
        # Find most visited page
        page_counts = {}
        for page in navigation:
            page_name = page["page"]
            page_counts[page_name] = page_counts.get(page_name, 0) + 1
        
        if page_counts:
            session["page_summary"]["most_visited_page"] = max(page_counts, key=page_counts.get)
        
        # Calculate bounce rate (single page session)
        session["page_summary"]["bounce_rate"] = len(navigation) == 1
        
        # Build traversal graph
        self._build_traversal_graph(session)
    
    def _build_traversal_graph(self, session):
        """Build traversal graph for the session"""
        navigation = session["navigation_sequence"]
        
        if len(navigation) < 2:
            return
        
        # Extract unique pages (nodes)
        nodes = list(set(page["page"] for page in navigation))
        session["traversal_graph"]["nodes"] = nodes
        
        # Build edges
        edges = {}
        for i in range(len(navigation) - 1):
            from_page = navigation[i]["page"]
            to_page = navigation[i + 1]["page"]
            edge_key = f"{from_page}->{to_page}"
            
            if edge_key not in edges:
                edges[edge_key] = {
                    "from": from_page,
                    "to": to_page,
                    "count": 0,
                    "total_time": 0
                }
            
            edges[edge_key]["count"] += 1
            edges[edge_key]["total_time"] += navigation[i].get("time_on_page", 0)
        
        # Calculate average time for edges
        for edge in edges.values():
            edge["avg_time"] = edge["total_time"] / edge["count"] if edge["count"] > 0 else 0
            del edge["total_time"]  # Remove total_time as we only need avg_time
        
        session["traversal_graph"]["edges"] = list(edges.values())
        
        # Build path
        path = [page["page"] for page in navigation]
        session["traversal_graph"]["paths"] = [{
            "path": path,
            "frequency": 1,
            "total_time": sum(page.get("time_on_page", 0) for page in navigation)
        }]
