# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 20:54:01 2020

@author: user
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from urllib.request import urlopen
import json
import networkx as nx
import plotly.graph_objects as go

#%%
df = pd.read_csv("C:\\Users\\user\\Downloads\\setup\\arxiv_models.csv")
strings = [
 x.split("//")[1].split("/")[-1].split(".pdf")[0] 
 if '.pdf' in x else x.split("//")[1].split("/")[-1]
 for x in df.loc[~pd.isnull(df['논문']), '논문'].values 
 if x.split("//")[1].split("/")[0] == "arxiv.org"]

#%%
text = dict()
for s in strings:
    url = "https://api.semanticscholar.org/v1/paper/arxiv:{}".format(s)
    response_text = urlopen(url)
    element = json.loads(response_text.read())
    text[element['title']] = element
        
#%%
#text2 = text.copy()
#for k, v in text.items():
#    url = "https://api.semanticscholar.org/v1/paper/arxiv:{}".format(v['arxivId'])
    
#%%
G = nx.DiGraph()

for t in text.keys():
    for r in text[t]['references']:
        G.add_edge(r['title'], t)
    for c in text[t]['citations']:
        G.add_edge(t, c['title'])

#%%
nodes_to_remove = []
for node in G.nodes():
    if (len(G.adj[node]) == 0):
        if node not in text.keys():
            nodes_to_remove.append(node)
        
for node in nodes_to_remove:
    G.remove_node(node)
        
#%%
pos = nx.spring_layout(G)
nx.draw_networkx(G, pos=pos, with_labels=False)
plt.show()

#%%
edge_x = []
edge_y = []
for edge in G.edges():
    x0, y0 = pos[edge[0]]
    x1, y1 = pos[edge[1]]
    edge_x.append(x0)
    edge_x.append(x1)
    edge_x.append(None)
    edge_y.append(y0)
    edge_y.append(y1)
    edge_y.append(None)

edge_trace = go.Scatter(
    x=edge_x, y=edge_y,
    line=dict(width=0.5, color='#888'),
    hoverinfo='none',
    mode='lines')
    
#%%
node_x = []
node_y = []
for node in G.nodes():
    x, y = pos[node]
    node_x.append(x)
    node_y.append(y)

node_trace = go.Scatter(
    x=node_x, y=node_y,
    mode='markers',
    hoverinfo='text',
    marker=dict(
        showscale=True,
        colorscale='YlGnBu',
        reversescale=True,
        color=[],
        size=10,
        colorbar=dict(
            thickness=15,
            title='# of references/citations',
            xanchor='left',
            titleside='right'
        ),
        line_width=2))
        
#%%
node_adjacencies = []
node_text = []
for node, adjacencies in enumerate(G.adjacency()):
    node_adjacencies.append(len(adjacencies[1]))
    sample_text = "Title: {}<br />".format(adjacencies[0])
    sample_text += '# of citations: '+str(len(adjacencies[1]))
    node_text.append(sample_text)

node_trace.marker.color = node_adjacencies
node_trace.text = node_text

#%%
fig = go.Figure(data=[edge_trace, node_trace],
             layout=go.Layout(
                title='<br>딥페이크 합성 모델 아카이브 논문 네트워크',
                titlefont_size=16,
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                annotations=[ dict(
                    text="인용된 논문에서 인용한 논문으로",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.005, y=-0.002 ) ],
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                )
    
fig.write_html('DeepFake_Generator_Figures.html', auto_open=True)