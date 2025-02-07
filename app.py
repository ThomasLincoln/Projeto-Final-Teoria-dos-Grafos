# app.py
from flask import Flask, request, render_template, redirect, url_for, flash, session
from grafo import Grafo
from pyvis.network import Network
import os
import networkx as nx
import random

app = Flask(__name__)
app.secret_key = "chave-secreta-qualquer"

grafo_atual = None  # variável global que armazena a instância atual do Grafo

@app.route("/", methods=["GET"])
def index():
    """
    Página inicial: mostra o formulário para upload do grafo e,
    se existir um HTML gerado (graph_html), exibe-o.
    """
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    if "arquivo_grafo" not in request.files:
        flash("Nenhum arquivo enviado", "danger")
        return redirect(url_for("index"))
    
    arquivo = request.files["arquivo_grafo"]
    if arquivo.filename == "":
        flash("Nenhum arquivo selecionado", "danger")
        return redirect(url_for("index"))
    
    try:
        conteudo = arquivo.read().decode("utf-8").splitlines()
        num_vertices = int(conteudo[0])
        grafo = Grafo(num_vertices)
        
        for i, linha in enumerate(conteudo[1:], start=1):
            u, v = map(int, linha.split())
            grafo.adicionar_aresta(u, v)
            
        global grafo_atual
        grafo_atual = grafo
        
        # Criar visualização
        net = Network(height="500px", width="100%", directed=False)
        
        # Adicionar nós
        for node_id in range(num_vertices):
            net.add_node(node_id, label=str(node_id), color="#79C2EC")
            
        # Adicionar arestas com labels alfabéticas
        for i, (u, v) in enumerate(grafo.arestas):
            label = chr(65 + i)  # Converte 0->A, 1->B, 2->C, etc.
            net.add_edge(u, v, label=label)
            
        # Opções de visualização incluindo labels nas arestas
        net.set_options("""
        var options = {
          "nodes": {
            "font": {
              "color": "rgba(0,0,0,1)"
            }
          },
          "edges": {
            "font": {
              "size": 12
            },
            "width": 2
          }
        }
        """)
        
        graph_html = net.generate_html()
        session['graph_html'] = graph_html
        
        flash("Grafo carregado com sucesso!", "success")
        return redirect(url_for("index"))
        
    except Exception as e:
        flash(f"Erro ao processar arquivo: {str(e)}", "danger")
        return redirect(url_for("index"))

@app.route("/gerar_arvore", methods=["POST"])
def gerar_arvore():
    global grafo_atual
    
    if grafo_atual is None:
        flash("Carregue um grafo primeiro!", "warning")
        return redirect(url_for("index"))
    
    # Criar grafo NetworkX
    G = nx.Graph()
    G.add_edges_from(grafo_atual.arestas)
    
    # Encontrar o centro do grafo
    centro = nx.center(G)[0]  # Pegamos o primeiro vértice do centro
    
    # Gerar árvore usando BFS a partir do centro
    arvore_arestas = []
    visitados = {centro}
    fila = [(centro, None)]  # (vértice, pai)
    
    while fila:
        vertice, pai = fila.pop(0)
        if pai is not None:
            arvore_arestas.append((pai, vertice))
        
        for vizinho in G[vertice]:
            if vizinho not in visitados:
                visitados.add(vizinho)
                fila.append((vizinho, vertice))
    
    # Criar visualização da árvore
    net_tree = Network(height="500px", width="100%", directed=False)
    vertices_na_arvore = set([v for aresta in arvore_arestas for v in aresta])
    
    # Adicionar nós - rosa para o centro, verde para os outros na árvore
    for node_id in range(grafo_atual.vertices):
        if node_id == centro:
            net_tree.add_node(node_id, label=str(node_id), color="#FF69B4")  # Rosa para o centro
        elif node_id in vertices_na_arvore:
            net_tree.add_node(node_id, label=str(node_id), color="#90EE90")  # Verde para nós na árvore
        else:
            net_tree.add_node(node_id, label=str(node_id), color="#79C2EC")  # Azul para outros
    
    # Adicionar todas as arestas - vermelhas para a árvore, cinza para as outras
    for i, (u, v) in enumerate(grafo_atual.arestas):
        label = chr(65 + i)
        if (u, v) in arvore_arestas or (v, u) in arvore_arestas:
            net_tree.add_edge(u, v, label=label, color="#FF0000")  # Vermelho para arestas na árvore
        else:
            net_tree.add_edge(u, v, label=label, color="#323232")  # Cinza para outras arestas
    
    # Configurar opções de visualização
    net_tree.set_options("""
    var options = {
      "nodes": {
        "font": {
          "color": "rgba(0,0,0,1)"
        }
      },
      "edges": {
        "font": {
          "size": 12
        },
        "width": 2
      }
    }
    """)
    
    # Salvar o HTML na sessão
    session['graph_html'] = net_tree.generate_html()
    session['is_tree_view'] = True
    
    flash(f"Árvore central gerada com sucesso! Centro no vértice {centro}", "success")
    return redirect(url_for("index"))

@app.route("/verificar_euleriano", methods=["POST"])
def verificar_euleriano():
    global grafo_atual
    
    if grafo_atual is None:
        flash("Carregue um grafo primeiro!", "warning")
        return redirect(url_for("index"))
    
    is_euler, mensagem = grafo_atual.is_euleriano()
    
    # Criar visualização
    net = Network(height="500px", width="100%", directed=False)
    
    # Gerar lista de adjacência para contar graus
    lista_adj = grafo_atual.gerar_lista_adjacencia()
    
    # Adicionar nós com cores baseadas no grau
    for node_id in range(grafo_atual.vertices):
        grau = len(lista_adj[node_id])
        if grau % 2 == 0:
            net.add_node(node_id, label=f"{node_id}\n(grau:{grau})", color="#FFA07A")  # Par
        else:
            net.add_node(node_id, label=f"{node_id}\n(grau:{grau})", color="#FF4500")  # Ímpar
    
    # Adicionar arestas com labels
    for i, (u, v) in enumerate(grafo_atual.arestas):
        label = chr(65 + i)
        net.add_edge(u, v, label=label)
    
    net.set_options("""
    var options = {
      "nodes": {
        "font": {
          "color": "rgba(0,0,0,1)",
          "size": 16,
          "face": "arial"
        }
      },
      "edges": {
        "font": {
          "size": 12
        },
        "width": 2
      }
    }
    """)
    
    graph_html = net.generate_html()
    session['graph_html'] = graph_html
    
    categoria = "success" if is_euler else "warning"
    flash(mensagem, categoria)
    return redirect(url_for("index"))

@app.route("/verificar_hamiltoniano", methods=["POST"])
def verificar_hamiltoniano():
    global grafo_atual
    
    if grafo_atual is None:
        flash("Carregue um grafo primeiro!", "warning")
        return redirect(url_for("index"))
    
    is_hamilton, mensagem = grafo_atual.is_hamiltoniano()
    
    # Criar visualização
    net = Network(height="500px", width="100%", directed=False)
    
    # Gerar lista de adjacência para contar graus
    lista_adj = grafo_atual.gerar_lista_adjacencia()
    
    # Adicionar nós com informação do grau
    for node_id in range(grafo_atual.vertices):
        grau = len(lista_adj[node_id])
        net.add_node(node_id, 
                    label=f"{node_id}\n(grau:{grau})", 
                    color="#98fb98" if is_hamilton else "#ffa07a")
    
    # Adicionar arestas com labels
    for i, (u, v) in enumerate(grafo_atual.arestas):
        label = chr(65 + i)
        net.add_edge(u, v, label=label)
    
    net.set_options("""
    var options = {
      "nodes": {
        "font": {
          "color": "rgba(0,0,0,1)",
          "size": 16,
          "face": "arial"
        }
      },
      "edges": {
        "font": {
          "size": 12
        },
        "width": 2
      }
    }
    """)
    
    graph_html = net.generate_html()
    session['graph_html'] = graph_html
    
    categoria = "success" if is_hamilton else "warning"
    flash(mensagem, categoria)
    return redirect(url_for("index"))

@app.route("/encontrar_corte", methods=["POST"])
def encontrar_corte():
    global grafo_atual
    
    if grafo_atual is None:
        flash("Carregue um grafo primeiro!", "warning")
        return redirect(url_for("index"))
    
    try:
        # Criar grafo NetworkX
        G = nx.Graph()
        G.add_edges_from(grafo_atual.arestas)
        
        # Obter árvore geradora mínima
        T = nx.minimum_spanning_tree(G)
        
        # Escolher uma aresta aleatória da árvore
        aresta_escolhida = random.choice(list(T.edges()))
        
        try:
            # Cria uma cópia da árvore e remove a aresta em questão
            T_modificada = T.copy()
            T_modificada.remove_edge(*aresta_escolhida)
            
            # Identifica as duas componentes resultantes da remoção
            componentes = list(nx.connected_components(T_modificada))
            if len(componentes) != 2:
                return None, "A aresta escolhida não gera um corte fundamental válido"
            
            comp1, comp2 = componentes
            
            # Encontra todas as arestas que cruzam o corte
            corte_fundamental = []
            for u in comp1:
                for v in G[u]:
                    if v in comp2:
                        corte_fundamental.append((min(u, v), max(u, v)))  # Ordena para evitar duplicatas
            
            # Criar visualização
            net = Network(height="500px", width="100%", directed=False)
            
            # Adicionar nós com cores diferentes para cada componente
            for node_id in range(grafo_atual.vertices):
                if node_id in comp1:
                    net.add_node(node_id, label=str(node_id), color="#98fb98")  # Verde
                else:
                    net.add_node(node_id, label=str(node_id), color="#ffa07a")  # Laranja
            
            # Adicionar arestas - vermelho para arestas do corte
            for i, (u, v) in enumerate(grafo_atual.arestas):
                label = chr(65 + i)
                if (u, v) in corte_fundamental or (v, u) in corte_fundamental:
                    net.add_edge(u, v, label=label, color="#FF0000", width=3)  # Vermelho e grosso
                else:
                    net.add_edge(u, v, label=label, color="#323232")  # Cinza
            
            net.set_options("""
            var options = {
              "nodes": {
                "font": {
                  "color": "rgba(0,0,0,1)"
                }
              },
              "edges": {
                "font": {
                  "size": 12
                },
                "width": 2
              }
            }
            """)
            
            graph_html = net.generate_html()
            session['graph_html'] = graph_html
            
            flash(f"Corte fundamental encontrado com {len(corte_fundamental)} arestas", "success")
            
        except Exception as e:
            flash(f"Erro ao encontrar corte fundamental: {str(e)}", "danger")
        
    except Exception as e:
        flash(f"Erro ao processar o corte fundamental: {str(e)}", "danger")
    
    return redirect(url_for("index"))

@app.route("/mostrar_original", methods=["POST"])
def mostrar_original():
    global grafo_atual
    
    if grafo_atual is None:
        flash("Carregue um grafo primeiro!", "warning")
        return redirect(url_for("index"))
    
    # Criar visualização do grafo original
    net = Network(height="500px", width="100%", directed=False)
    
    # Adicionar nós
    for node_id in range(grafo_atual.vertices):
        net.add_node(node_id, label=str(node_id), color="#79C2EC")
    
    # Adicionar arestas com labels alfabéticas
    for i, (u, v) in enumerate(grafo_atual.arestas):
        label = chr(65 + i)  # Converte 0->A, 1->B, 2->C, etc.
        net.add_edge(u, v, label=label)
    
    net.set_options("""
    var options = {
      "nodes": {
        "font": {
          "color": "rgba(0,0,0,1)"
        }
      },
      "edges": {
        "font": {
          "size": 12
        },
        "width": 2
      }
    }
    """)
    
    # Atualizar o graph_html com o grafo original
    session['graph_html'] = net.generate_html()
    session['is_tree_view'] = False

    flash("Visualização original do grafo restaurada", "success")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
