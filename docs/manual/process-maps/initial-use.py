import pygraphviz as pgv
G = pgv.AGraph('initial-use.dot')
G.layout('dot')
G.draw('initial-use.png')
