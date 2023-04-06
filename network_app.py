import networkx as nx
from pyvis.network import Network
import sqlite3
from sqlite3 import Error
from flask import Flask, render_template, request, jsonify
app = Flask(__name__)

G = nx.Graph()

# Creates connection to sqlite database
def create_connection():
    conn = None;
    try:
        conn = sqlite3.connect('network_graph.db')
    except Error as e:
        print(e)
    return conn

#Initates DB tables
def init_database():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT NOT NULL UNIQUE,
            info TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source INTEGER NOT NULL,
            target INTEGER NOT NULL,
            FOREIGN KEY (source) REFERENCES nodes (id),
            FOREIGN KEY (target) REFERENCES nodes (id),
            UNIQUE (source, target)
        )
    """)
    conn.commit()
    conn.close()

init_database()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/add_node", methods=["POST"])
def add_node():
    node = request.form["node"]
    info = request.form.get("info", "")
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO nodes (label, info) VALUES (?, ?)", (node, info))
    conn.commit()
    conn.close()
    return jsonify(success=True)

@app.route("/delete_node", methods=["POST"])
def delete_node():
    node = request.form["node"]
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM nodes WHERE label = ?", (node,))
    cursor.execute("DELETE FROM edges WHERE source IN (SELECT id FROM nodes WHERE label = ?) OR target IN (SELECT id FROM nodes WHERE label = ?)", (node, node))
    conn.commit()
    conn.close()
    return jsonify(success=False)

@app.route("/update_node_info", methods=["POST"])
def update_node_info():
    node = request.form["node"]
    info = request.form["info"]
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE nodes SET info = ? WHERE label = ?", (info, node))
    conn.commit()
    conn.close()
    return jsonify(success=True)


@app.route("/visualize_network")
def visualize_network():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, label, info FROM nodes")
    nodes = cursor.fetchall()
    cursor.execute("SELECT source, target FROM edges")
    edges = cursor.fetchall()
    conn.close()

    G.clear()
    for node in nodes:
        G.add_node(node[1], info=node[2])

    for edge in edges:
        source_node = [n[1] for n in nodes if n[0] == edge[0]][0]
        target_node = [n[1] for n in nodes if n[0] == edge[1]][0]
        G.add_edge(source_node, target_node)

    net = Network(notebook=True)
    net.from_nx(G)
    for node in net.nodes:
        node["color"] = "red"
        node["size"] = 20
        node["title"] = G.nodes[node["id"]].get("info", "")
    net.save_graph("static/network_visualization.html")
    return jsonify(success=True)

@app.route("/add_edge", methods=["POST"])
def add_edge():
    source = request.form["source"]
    target = request.form["target"]
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO edges (source, target) SELECT n1.id, n2.id FROM nodes AS n1, nodes AS n2 WHERE n1.label = ? AND n2.label = ?", (source, target))
    conn.commit()
    conn.close()
    return jsonify(success=True)

@app.route("/delete_edge", methods=["POST"])
def delete_edge():
    source = request.form["source"]
    target = request.form["target"]
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM edges WHERE id IN (SELECT e.id FROM edges AS e JOIN nodes AS n1 ON e.source = n1.id JOIN nodes AS n2 ON e.target = n2.id WHERE n1.label = ? AND n2.label = ?)", (source, target))
    conn.commit()
    conn.close()
    return jsonify(success=True)


if __name__ == "__main__":
    app.run(debug=True)
