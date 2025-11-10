try:
    import kuzu
except Exception as _e:
    kuzu = None
    # Defer raising until someone tries to instantiate KuzuDB so the module can be imported
    # in environments where kuzu isn't available (for tooling, tests, or Docker build steps).
from typing import List, Optional, Dict, Any

class KuzuDB:
    def __init__(self, db_path: str):
        if kuzu is None:
            raise ImportError("kuzu package is required to use KuzuDB. Install it in your environment.")

        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        self._init_schema()

    def _init_schema(self):
        """Initialize graph schema if not exists"""
        try:
            # Check if tables already exist
            result = self.conn.execute("CALL SHOW_TABLES() RETURN *")
            existing_tables = [row[0] for row in result]
            
            # Create NODE table for links if it doesn't exist
            if 'links' not in existing_tables:
                self.conn.execute("""
                    CREATE NODE TABLE links(
                        link STRING,
                        session_id STRING,
                        title STRING,
                        summary STRING,
                        embedding_id STRING,
                        PRIMARY KEY (link)
                    )
                """)
                print("Created 'links' node table")
            
            # Create REL table for hyperlinks if it doesn't exist
            if 'hyprlink' not in existing_tables:
                self.conn.execute("""
                    CREATE REL TABLE hyprlink(
                        FROM links TO links,
                        session_id STRING
                    )
                """)
                print("Created 'hyprlink' relationship table")
        except Exception as e:
            # Only print error if it's not about tables already existing
            if "already exists" not in str(e):
                print(f"Schema init error: {e}")

    def show(self, query: str) -> List:
        """Execute query and return results"""
        try:
            result = self.conn.execute(query)
            return list(result)
        except Exception as e:
            print(f"Query error: {e}")
            return []

    def insert_rel(self, link1: str, link2: str, session_id: str):
        """Insert relationship between two links"""
        try:
            link1_safe = self._escape(link1)
            link2_safe = self._escape(link2)
            session_safe = self._escape(session_id)
            
            query = f"""
                MATCH (l1:links {{link:'{link1_safe}', session_id:'{session_safe}'}}),
                      (l2:links {{link:'{link2_safe}', session_id:'{session_safe}'}})
                CREATE (l1)-[:hyprlink {{session_id:'{session_safe}'}}]->(l2)
            """
            self.conn.execute(query)
        except Exception as e:
            print(f"Insert relationship error: {e}")

    def insert_node(self, link: str, session_id: str):
        """Insert node into graph"""
        try:
            link_safe = self._escape(link)
            session_safe = self._escape(session_id)
            
            query = f"""
                CREATE (n:links {{
                    link:'{link_safe}',
                    session_id:'{session_safe}',
                    title:'',
                    summary:'',
                    embedding_id:''
                }})
            """
            self.conn.execute(query)
        except Exception as e:
            print(f"Insert node error: {e}")

    def get_neighbors(self, link: str, session_id: str, depth: int = 1) -> List[str]:
        """Get connected nodes within specified depth"""
        try:
            link_safe = self._escape(link)
            session_safe = self._escape(session_id)
            
            query = f"""
                MATCH (start:links {{link:'{link_safe}', session_id:'{session_safe}'}})
                       -[:hyprlink*1..{depth}]->
                       (neighbor:links {{session_id:'{session_safe}'}})
                RETURN neighbor.link
            """
            results = self.show(query)
            return [r[0] if isinstance(r, (list, tuple)) else r.get('neighbor.link', '') for r in results]
        except Exception as e:
            print(f"Get neighbors error: {e}")
            return []

    def get_session_nodes(self, session_id: str) -> List[str]:
        """Get all nodes in a session"""
        try:
            session_safe = self._escape(session_id)
            query = f"MATCH (n:links {{session_id:'{session_safe}'}}) RETURN n.link"
            results = self.show(query)
            return [r[0] if isinstance(r, (list, tuple)) else r.get('n.link', '') for r in results]
        except Exception as e:
            print(f"Get session nodes error: {e}")
            return []

    def test(self):
        """Test connection"""
        try:
            result = self.conn.execute("CALL SHOW_TABLES() RETURN *")
            print(list(result))
        except Exception as e:
            print(f"Test failed: {e}")

    def _escape(self, text: str) -> str:
        """Escape single quotes in strings"""
        if not isinstance(text, str):
            text = str(text)
        return text.replace("'", "\\'")

    def __del__(self):
        """Close connection"""
        try:
            self.conn.close()
        except:
            pass