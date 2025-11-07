import kuzu
from typing import List, Optional, Dict, Any

class KuzuDB:
    def __init__(self, db_path: str):
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        self._init_schema()

    def _init_schema(self):
        """Initialize graph schema if not exists"""
        try:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS links (
                    link STRING PRIMARY KEY,
                    session_id STRING,
                    title STRING,
                    summary STRING,
                    embedding_id STRING
                )
            """)
            
            self.conn.execute("""
                CREATE REL TABLE IF NOT EXISTS hyprlink (
                    FROM links TO links,
                    session_id STRING
                )
            """)
        except Exception as e:
            print(f"Schema init info: {e}")

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