import kuzu

class KuzuDB:
    def __init__(self, db: kuzu.Database) -> None:
        self.conn = kuzu.Connection(db)

    def show(self, query):
        result = self.conn.execute(query)
        return list(result)

    def insert_rel(self, link1, link2, session_id):
        self.conn.execute(f"match (l1:links {{link:'{link1}', session_id:{session_id}}}), (l2:links {{link:'{link2}', session_id:{session_id}}}) CREATE (l1)-[:hyprlink {{session_id: '{session_id}'}}]->(l2);")
        return

    def insert_node(self, link, session_id):
        self.conn.execute(f"CREATE (n:links {{link: '{link}', session_id: '{session_id}'}});")
        return

    def test(self):
        result = self.conn.execute("CALL SHOW_TABLES() RETURN *")
        print(list(result))
        return
    
    def __del__(self):
        self.conn.close()
        return

if __name__ == "__main__":
    db = kuzu.Database("sites.kuzu");
    c = KuzuDB(db);
