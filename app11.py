from flask import Flask, render_template, request
import networkx as nx
import pandas as pd
import plotly.graph_objects as go
import json

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index11.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    file = request.files['file']
    transactions = pd.read_csv(file)

    G = nx.Graph()
    for index, row in transactions.iterrows():
        G.add_edge(row['Sender'], row['Receiver'], weight=row['Amount'])

    clusters = nx.algorithms.community.asyn_lpa_communities(G)

    suspicious_transactions = []
    non_suspicious_transactions = []
    for cluster in clusters:
        for node in cluster:
            if G.degree(node) > 17:  # arbitrary threshold
                suspicious_transactions.append(node)
            else:
                non_suspicious_transactions.append(node)

    nodes = list(G.nodes())
    sankey_data = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=[node for node in G.nodes()],
            color="blue"
        ),
        link=dict(
            source=[nodes.index(edge[0]) for edge in G.edges()],
            target=[nodes.index(edge[1]) for edge in G.edges()],
            value=[edge[2]['weight'] for edge in G.edges(data=True)]
        )
    )])

    # Add annotations for suspicious and non-suspicious transactions
    sankey_data.update_layout(
        title_text="Transaction Flow",
        font_size=10,
        annotations=[
            dict(
                x=0.5,
                y=1.1,
                xref='paper',
                yref='paper',
                text=f"Suspicious Transactions: {len(suspicious_transactions)}",
                showarrow=False,
                font=dict(size=14)
            ),
            dict(
                x=0.5,
                y=1.05,
                xref='paper',
                yref='paper',
                text=f"Non-Suspicious Transactions: {len(non_suspicious_transactions)}",
                showarrow=False,
                font=dict(size=14)
            )
        ]
    )

    # Convert the Plotly figure to JSON
    fig_json = sankey_data.to_plotly_json()

    # Convert the JSON data to a string for rendering in the template
    sankey_json_str = json.dumps(fig_json)

    subgraph_hashes = {}
    for node in suspicious_transactions:
        subgraph = G.subgraph([node])
        subgraph_hash = nx.algorithms.graph_hashing.weisfeiler_lehman_graph_hash(subgraph)
        subgraph_hashes[node] = subgraph_hash

    return render_template('results11.html', 
                           suspicious_transactions=suspicious_transactions, 
                           sankey_data=sankey_json_str, 
                           subgraph_hashes=subgraph_hashes)

if __name__ == '__main__':
    app.run(debug=True)
