# app.py
from flask import Flask, request, render_template, redirect, url_for, flash, session
from grafo import Grafo
from pyvis.network import Network
import os
import networkx as nx
import random
from tempfile import gettempdir
import uuid
import json

app = Flask(__name__)
app.secret_key = "chave-secreta-qualquer"

grafo_atual = None  # variável global que armazena a instância atual do Grafo
mapa_vertices = {}  # mapeia nomes para IDs
mapa_reverso = {}  # mapeia IDs para nomes

# Configurações globais
TEMP_DIR = os.path.join(app.static_folder, 'temp_graphs')
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

def gerar_label_aresta(indice):
    return str(indice + 1) 

def salvar_visualizacao(net, is_tree_view=False):
    """
    Função auxiliar para salvar a visualização em arquivo temporário e limpar arquivos antigos
    """
    try:
        # Limpar todos os arquivos temporários antigos
        for arquivo in os.listdir(TEMP_DIR):
            if arquivo.startswith('graph_') and arquivo.endswith('.html'):
                caminho_arquivo = os.path.join(TEMP_DIR, arquivo)
                try:
                    os.remove(caminho_arquivo)
                    print(f"Arquivo temporário removido: {caminho_arquivo}")
                except Exception as e:
                    print(f"Erro ao remover arquivo {caminho_arquivo}: {e}")
        
        # Gerar novo arquivo
        session_id = str(uuid.uuid4())
        filename = f'graph_{session_id}.html'
        temp_file_path = os.path.join(TEMP_DIR, filename)
        
        # Salvar novo arquivo
        net.save_graph(temp_file_path)
        print(f"Novo arquivo salvo: {temp_file_path}")
        
        # Atualizar sessão
        session['graph_filename'] = filename
        session['is_tree_view'] = is_tree_view
        
        return True
    except Exception as e:
        print(f"Erro ao salvar visualização: {e}")
        return False

@app.route("/")
def index():
    global grafo_atual
    info_grafo = calcular_info_grafo(grafo_atual) if grafo_atual else None
    return render_template(
        "index.html",
        graph_filename=session.get('graph_filename'),
        grafo_atual=grafo_atual,
        info_grafo=info_grafo
    )

@app.route("/upload", methods=["POST"])
def upload():
    global grafo_atual, mapa_vertices, mapa_reverso
    
    if "arquivo_grafo" not in request.files:
        flash("Nenhum arquivo de grafo enviado", "danger")
        return redirect(url_for("index"))
    
    arquivo = request.files["arquivo_grafo"]
    if arquivo.filename == "":
        flash("Nenhum arquivo de grafo selecionado", "danger")
        return redirect(url_for("index"))
    
    try:
        # Tenta diferentes codificações
        codificacoes = ['utf-8', 'utf-16', 'latin1', 'cp1252']
        conteudo = None
        
        for encoding in codificacoes:
            try:
                arquivo.seek(0)
                conteudo = arquivo.read().decode(encoding).splitlines()
                break
            except UnicodeDecodeError:
                continue
        
        if conteudo is None:
            flash("Não foi possível decodificar o arquivo. Tente salvá-lo como UTF-8.", "danger")
            return redirect(url_for("index"))
            
        num_vertices = int(conteudo[0])
        print(f"Número de vértices: {num_vertices}")  # Log
        
        # Reset dos mapeamentos
        mapa_vertices = {}
        mapa_reverso = {}
        vertices_unicos = set()
        
        # Primeira passagem: coletar todos os nomes únicos de vértices
        for linha in conteudo[1:]:
            try:
                v1, v2 = [nome.strip().strip('"') for nome in linha.split('"') if nome.strip()]
                vertices_unicos.add(v1)
                vertices_unicos.add(v2)
            except Exception as e:
                print(f"Erro ao processar linha: {linha}")  # Log
                print(f"Erro: {str(e)}")  # Log
                raise
        
        print(f"Vértices únicos encontrados: {len(vertices_unicos)}")  # Log
        
        # Verifica se o número de vértices corresponde
        if len(vertices_unicos) != num_vertices:
            flash(f"Número de vértices declarado ({num_vertices}) não corresponde ao número de vértices únicos encontrados ({len(vertices_unicos)})", "danger")
            return redirect(url_for("index"))
        
        # Cria mapeamento de nomes para IDs
        for idx, nome in enumerate(sorted(vertices_unicos)):
            mapa_vertices[nome] = idx
            mapa_reverso[idx] = nome
        
        # Cria o grafo
        grafo = Grafo(num_vertices)
        
        # Segunda passagem: adicionar arestas usando os IDs mapeados
        for linha in conteudo[1:]:
            v1, v2 = [nome.strip().strip('"') for nome in linha.split('"') if nome.strip()]
            u = mapa_vertices[v1]
            v = mapa_vertices[v2]
            grafo.adicionar_aresta(u, v)
        
        grafo_atual = grafo
        print(f"Número de arestas: {len(grafo.arestas)}")  # Log
        
        # Criar visualização com configurações otimizadas
        net = Network(
            height="800px",  # Aumentado
            width="100%",
            directed=False,
            bgcolor="#ffffff",
            font_color="#000000"
        )
        
        # Configurações de física para melhor distribuição
        net.set_options("""
        var options = {
          "nodes": {
            "font": {
              "size": 12,
              "color": "rgba(0,0,0,1)"
            },
            "size": 20
          },
          "edges": {
            "font": {
              "size": 10
            },
            "width": 1,
            "smooth": {
              "type": "continuous",
              "forceDirection": "none"
            }
          },
          "physics": {
            "forceAtlas2Based": {
              "gravitationalConstant": -50,
              "centralGravity": 0.01,
              "springLength": 200,
              "springConstant": 0.08
            },
            "maxVelocity": 50,
            "solver": "forceAtlas2Based",
            "timestep": 0.35,
            "stabilization": {
              "enabled": true,
              "iterations": 1000
            }
          }
        }
        """)
        
        # Adicionar nós
        for node_id in range(num_vertices):
            nome = mapa_reverso[node_id]
            net.add_node(
                node_id,
                label=nome,
                color="#79C2EC",
                title=nome,
                size=20
            )
        
        for i, (u, v) in enumerate(grafo.arestas):
            label = gerar_label_aresta(i)
            net.add_edge(u, v, label=label)
        
        # Salvar visualização
        salvar_visualizacao(net)
        
        flash(f"Grafo carregado com sucesso! ({num_vertices} vértices, {len(grafo.arestas)} arestas)", "success")
        return redirect(url_for("index"))
        
    except Exception as e:
        print(f"Erro detalhado: {str(e)}")  # Log
        flash(f"Erro ao processar arquivo do grafo: {str(e)}", "danger")
        return redirect(url_for("index"))

@app.route("/gerar_arvore", methods=["POST"])
def gerar_arvore():
    global grafo_atual, mapa_vertices, mapa_reverso
    
    if grafo_atual is None:
        flash("Carregue um grafo primeiro!", "warning")
        return redirect(url_for("index"))
    
    try:
        # Criar grafo NetworkX
        G = nx.Graph()
        G.add_edges_from(grafo_atual.arestas)
        
        # Gerar árvore geradora mínima
        T = nx.minimum_spanning_tree(G)
        arestas_arvore = list(T.edges())
        
        # Escolher um vértice central (pode ser o de maior grau)
        centro = max(T.degree, key=lambda x: x[1])[0]
        
        # Criar visualização
        net_tree = Network(height="500px", width="100%", directed=False)
        
        # Conjunto para rastrear vértices na árvore
        vertices_na_arvore = set()
        for u, v in arestas_arvore:
            vertices_na_arvore.add(u)
            vertices_na_arvore.add(v)
        
        # Adicionar nós - rosa para o centro, verde para os outros na árvore
        for node_id in range(grafo_atual.vertices):
            nome = mapa_reverso[node_id]
            if node_id == centro:
                net_tree.add_node(node_id, label=nome, color="#FF69B4", title=nome)  # Rosa para o centro
            elif node_id in vertices_na_arvore:
                net_tree.add_node(node_id, label=nome, color="#90EE90", title=nome)  # Verde para nós na árvore
            else:
                net_tree.add_node(node_id, label=nome, color="#79C2EC", title=nome)  # Azul para outros
        
        # Adicionar arestas da árvore com labels numéricas
        for i, (u, v) in enumerate(arestas_arvore):
            label = gerar_label_aresta(i)
            net_tree.add_edge(u, v, label=label, color="#90EE90", width=2)
        
        # Adicionar outras arestas em cinza
        for i, (u, v) in enumerate(grafo_atual.arestas):
            if (u, v) not in arestas_arvore and (v, u) not in arestas_arvore:
                label = gerar_label_aresta(i + len(arestas_arvore))
                net_tree.add_edge(u, v, label=label, color="#D3D3D3", width=1)
        
        net_tree.set_options("""
        var options = {
          "nodes": {
            "font": {
              "size": 12,
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
        
        # Salvar visualização
        salvar_visualizacao(net_tree, is_tree_view=True)
        
        flash("Árvore geradora mínima gerada com sucesso!", "success")
        return redirect(url_for("index"))
        
    except Exception as e:
        flash(f"Erro ao gerar árvore: {str(e)}", "danger")
        return redirect(url_for("index"))

@app.route("/verificar_euleriano", methods=["POST"])
def verificar_euleriano():
    global grafo_atual, mapa_vertices, mapa_reverso
    
    if grafo_atual is None:
        flash("Carregue um grafo primeiro!", "warning")
        return redirect(url_for("index"))
    
    try:
        eh_euleriano, mensagem = grafo_atual.is_euleriano()
        
        # Criar visualização
        net = Network(height="500px", width="100%", directed=False)
        
        # Gerar lista de adjacência para contar graus
        lista_adj = grafo_atual.gerar_lista_adjacencia()
        
        # Adicionar nós com cores baseadas no grau
        for node_id in range(grafo_atual.vertices):
            nome = mapa_reverso[node_id]
            grau = len(lista_adj[node_id])
            cor = "#90EE90" if grau % 2 == 0 else "#FFA07A"  # Verde para par, laranja para ímpar
            net.add_node(node_id, label=nome, color=cor, title=f"{nome} (grau: {grau})")
        
        # Adicionar arestas com labels numéricas
        for i, (u, v) in enumerate(grafo_atual.arestas):
            label = gerar_label_aresta(i)
            if len(lista_adj[u]) % 2 == 0 and len(lista_adj[v]) % 2 == 0:
                net.add_edge(u, v, label=label, color="#90EE90")
            else:
                net.add_edge(u, v, label=label, color="#FFA07A")
        
        net.set_options("""
        var options = {
          "nodes": {
            "font": {
              "size": 12,
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
        
        # Salvar visualização
        salvar_visualizacao(net)
        
        flash(mensagem, "info")
        return redirect(url_for("index"))
        
    except Exception as e:
        flash(f"Erro ao verificar grafo euleriano: {str(e)}", "danger")
        return redirect(url_for("index"))

@app.route("/verificar_hamiltoniano", methods=["POST"])
def verificar_hamiltoniano():
    global grafo_atual
    
    if grafo_atual is None:
        flash("Carregue um grafo primeiro!", "warning")
        return redirect(url_for("index"))
    
    try:
        net = configurar_network()
        
        # Gerar lista de adjacência
        lista_adj = grafo_atual.gerar_lista_adjacencia()
        
        # Verificar número de vértices com grau 1
        grau_1 = sum(1 for vizinhos in lista_adj.values() if len(vizinhos) == 1)
        if grau_1 > 2:
            flash("O grafo não é hamiltoniano, pois possui mais de dois vértices com grau 1.", "warning")
            return redirect(url_for("index"))
        
        # Verificar se é hamiltoniano
        vertices = list(range(grafo_atual.vertices))
        caminho = []
        visitados = set()
        
        def backtrack(vertice_atual):
            caminho.append(vertice_atual)
            visitados.add(vertice_atual)
            
            if len(caminho) == grafo_atual.vertices:
                # Verifica se forma um ciclo
                if caminho[0] in lista_adj[caminho[-1]]:
                    return True
                
            for vizinho in lista_adj[vertice_atual]:
                if vizinho not in visitados:
                    if backtrack(vizinho):
                        return True
            
            caminho.pop()
            visitados.remove(vertice_atual)
            return False
        
        # Tenta encontrar um ciclo hamiltoniano
        e_hamiltoniano = backtrack(0)
        
        # Adicionar nós
        for node_id in range(grafo_atual.vertices):
            label = mapa_reverso[node_id]
            net.add_node(node_id, label=label, color="#79C2EC", title=label)
        
        # Adicionar arestas
        for i, (u, v) in enumerate(grafo_atual.arestas):
            label = gerar_label_aresta(i)
            if e_hamiltoniano and ((u in caminho and v == caminho[caminho.index(u)+1]) or 
                                 (v in caminho and u == caminho[caminho.index(v)+1])):
                net.add_edge(u, v, label=label, color="#90EE90", width=3)  # Verde para o caminho
            else:
                net.add_edge(u, v, label=label, color="#323232")  # Cinza para outras arestas
        
        # Salvar visualização
        salvar_visualizacao(net)
        
        mensagem = "O grafo é hamiltoniano!" if e_hamiltoniano else "O grafo não é hamiltoniano."
        flash(mensagem, "success" if e_hamiltoniano else "warning")
        return redirect(url_for("index"))
        
    except Exception as e:
        flash(f"Erro ao verificar grafo hamiltoniano: {str(e)}", "danger")
        return redirect(url_for("index"))


@app.route("/encontrar_menor_corte", methods=["POST"])
def encontrar_menor_corte():
    global grafo_atual
    
    if grafo_atual is None:
        flash("Carregue um grafo primeiro!", "warning")
        return redirect(url_for("index"))
    
    try:
        # Criar visualização
        net = configurar_network()
        
        def eh_corte(arestas_corte, lista_adj):
            # Criar grafo temporário removendo as arestas do corte
            grafo_temp = {v: lista_adj[v].copy() for v in lista_adj}
            
            # Remover as arestas do corte
            for u, v in arestas_corte:
                if v in grafo_temp[u]:
                    grafo_temp[u].remove(v)
                if u in grafo_temp[v]:
                    grafo_temp[v].remove(u)
            
            # BFS para verificar conectividade
            visitados = set()
            fila = [0]
            visitados.add(0)
            
            while fila:
                v = fila.pop(0)
                for u in grafo_temp[v]:
                    if u not in visitados:
                        visitados.add(u)
                        fila.append(u)
            
            return len(visitados) != grafo_atual.vertices
        
        # Encontrar o menor corte possível
        lista_adj = grafo_atual.gerar_lista_adjacencia()
        todas_arestas = [(u, v) for u, v in grafo_atual.arestas]
        menor_corte = None
        
        # Testar cortes de tamanho crescente
        from itertools import combinations
        for tamanho in range(1, len(todas_arestas) + 1):
            print(f"Testando cortes de tamanho {tamanho}...")  # Debug
            for arestas_candidatas in combinations(todas_arestas, tamanho):
                if eh_corte(arestas_candidatas, lista_adj):
                    menor_corte = list(arestas_candidatas)
                    break
            if menor_corte:
                break
        
        if menor_corte:
            # Adicionar nós
            for node_id in range(grafo_atual.vertices):
                nome = mapa_reverso[node_id]
                net.add_node(node_id, label=nome, color="#79C2EC", title=nome)
            
            # Adicionar arestas - vermelho para arestas do corte
            for i, (u, v) in enumerate(grafo_atual.arestas):
                label = gerar_label_aresta(i)
                if (u, v) in menor_corte or (v, u) in menor_corte:
                    net.add_edge(u, v, label=label, color="#FF0000", width=3)  # Vermelho e grosso
                else:
                    net.add_edge(u, v, label=label, color="#323232")  # Cinza
            
            # Salvar visualização
            salvar_visualizacao(net)
            
            mensagem = f"Encontrado o menor corte possível com {len(menor_corte)} aresta(s)!"
            flash(mensagem, "success")
        else:
            flash("Não foi possível encontrar um corte no grafo.", "warning")
            
        return redirect(url_for("index"))
        
    except Exception as e:
        flash(f"Erro ao encontrar menor corte: {str(e)}", "danger")
        return redirect(url_for("index"))

@app.route("/mostrar_original", methods=["POST"])
def mostrar_original():
    global grafo_atual
    
    if grafo_atual is None:
        flash("Carregue um grafo primeiro!", "warning")
        return redirect(url_for("index"))
    
    try:
        print("Iniciando mostrar_original()")  # Debug
        
        net = configurar_network()
        print("Network configurado com sucesso")  # Debug
        
        # Adicionar nós
        print(f"Adicionando {grafo_atual.vertices} nós")  # Debug
        for node_id in range(grafo_atual.vertices):
            label = mapa_reverso[node_id]
            print(f"Adicionando nó {node_id} com label {label}")  # Debug
            net.add_node(node_id, label=label, color="#79C2EC", title=label)
        
        # Adicionar arestas
        print(f"Adicionando {len(grafo_atual.arestas)} arestas")  # Debug
        for i, (u, v) in enumerate(grafo_atual.arestas):
            label = gerar_label_aresta(i)
            print(f"Adicionando aresta {u}->{v} com label {label}")  # Debug
            net.add_edge(u, v, label=label, title=label)
        
        print("Salvando visualização")  # Debug
        salvar_visualizacao(net)
        
        flash("Visualização original do grafo restaurada", "success")
        return redirect(url_for("index"))
        
    except Exception as e:
        import traceback
        print("Erro detalhado:")  # Debug
        print(traceback.format_exc())  # Debug
        flash(f"Erro ao mostrar grafo original: {str(e)}", "danger")
        return redirect(url_for("index"))

@app.route("/limpar_grafo", methods=["POST"])
def limpar_grafo():
    if 'graph_filename' in session:
        try:
            # Remove o arquivo antigo
            filepath = os.path.join(TEMP_DIR, session['graph_filename'])
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"Erro ao remover arquivo: {e}")
    
    # Limpa as variáveis globais e sessão
    global grafo_atual, mapa_vertices, mapa_reverso
    grafo_atual = None
    mapa_vertices = {}
    mapa_reverso = {}
    session.clear()
    
    flash("Grafo removido com sucesso!", "success")
    return redirect(url_for("index"))

def configurar_network():
    """
    Função auxiliar para criar e configurar o Network
    """
    net = Network(
        height="800px",
        width="100%",
        directed=False,
        bgcolor="#ffffff"
    )
    
    options = """
    {
      "nodes": {
        "font": {
          "size": 12
        }
      },
      "edges": {
        "font": {
          "size": 12
        }
      },
      "physics": {
        "enabled": true,
        "stabilization": true
      }
    }
    """
    
    print("JSON das opções:", options)  # Debug
    print("Tamanho:", len(options))     # Debug
    print("Caractere na posição 443:", options[443] if len(options) > 443 else "N/A")  # Debug
    
    net.set_options(options)
    
    net.html = net.html.replace('<style type="text/css">', '''
    <style type="text/css">
    #mynetwork {
        height: 100vh !important;
    }
    </style>
    ''')
    
    return net

@app.route("/encontrar_corte_especifico", methods=["POST"])
def encontrar_corte_especifico():
    global grafo_atual
    
    if grafo_atual is None:
        flash("Carregue um grafo primeiro!", "warning")
        return redirect(url_for("index"))
    
    try:
        # Pegar o número de arestas desejado do form
        num_arestas = int(request.form.get('num_arestas', 1))
        
        # Criar visualização
        net = configurar_network()
        
        # Encontrar todos os possíveis cortes com o número específico de arestas
        def encontrar_cortes_tamanho_n(grafo, n):
            from itertools import combinations
            
            # Gerar lista de adjacência
            lista_adj = grafo.gerar_lista_adjacencia()
            
            # Função para verificar se um conjunto de arestas é um corte
            def eh_corte(arestas_corte):
                # Criar grafo temporário removendo as arestas do corte
                grafo_temp = {v: lista_adj[v].copy() for v in lista_adj}
                
                # Remover as arestas do corte
                for u, v in arestas_corte:
                    if v in grafo_temp[u]:
                        grafo_temp[u].remove(v)
                    if u in grafo_temp[v]:
                        grafo_temp[v].remove(u)
                
                # BFS para verificar conectividade
                visitados = set()
                fila = [0]  # Começa do vértice 0
                visitados.add(0)
                
                while fila:
                    v = fila.pop(0)
                    for u in grafo_temp[v]:
                        if u not in visitados:
                            visitados.add(u)
                            fila.append(u)
                
                # Se não visitou todos os vértices, é um corte
                return len(visitados) != grafo.vertices
            
            # Testar todas as combinações possíveis de n arestas
            todas_arestas = [(u, v) for u, v in grafo.arestas]
            for arestas_candidatas in combinations(todas_arestas, n):
                if eh_corte(arestas_candidatas):
                    return list(arestas_candidatas)
            
            return None
        
        # Tentar encontrar um corte com o número específico de arestas
        corte = encontrar_cortes_tamanho_n(grafo_atual, num_arestas)
        
        if corte:
            mensagem = f"Encontrado um corte com {num_arestas} aresta(s)!"
        else:
            mensagem = f"Não foi encontrado nenhum corte com {num_arestas} aresta(s)."
        
        # Adicionar nós
        for node_id in range(grafo_atual.vertices):
            nome = mapa_reverso[node_id]
            net.add_node(node_id, label=nome, color="#79C2EC", title=nome)
        
        # Adicionar arestas - vermelho para arestas do corte
        for i, (u, v) in enumerate(grafo_atual.arestas):
            label = gerar_label_aresta(i)
            if corte and ((u, v) in corte or (v, u) in corte):
                net.add_edge(u, v, label=label, color="#FF0000", width=3)  # Vermelho e grosso
            else:
                net.add_edge(u, v, label=label, color="#323232")  # Cinza
        
        # Salvar visualização
        salvar_visualizacao(net)
        
        flash(mensagem, "success" if corte else "warning")
        return redirect(url_for("index"))
        
    except Exception as e:
        flash(f"Erro ao encontrar corte: {str(e)}", "danger")
        return redirect(url_for("index"))

def calcular_diametro(grafo):
    """
    Calcula o diâmetro do grafo usando o algoritmo de Floyd-Warshall
    Retorna -1 se o grafo não for conexo
    """
    if not grafo or grafo.vertices == 0:
        return -1
        
    # Inicializa a matriz de distâncias
    INF = float('inf')
    dist = [[INF] * grafo.vertices for _ in range(grafo.vertices)]
    
    # Distância de um vértice para ele mesmo é 0
    for i in range(grafo.vertices):
        dist[i][i] = 0
    
    # Inicializa as distâncias das arestas existentes como 1
    for u, v in grafo.arestas:
        dist[u][v] = 1
        dist[v][u] = 1  # Grafo não direcionado
    
    # Algoritmo de Floyd-Warshall
    for k in range(grafo.vertices):
        for i in range(grafo.vertices):
            for j in range(grafo.vertices):
                if dist[i][k] != INF and dist[k][j] != INF:
                    dist[i][j] = min(dist[i][j], dist[i][k] + dist[k][j])
    
    # Encontra o maior caminho mínimo (diâmetro)
    diametro = 0
    for i in range(grafo.vertices):
        for j in range(grafo.vertices):
            if dist[i][j] == INF:  # Se houver vértices desconectados
                return -1
            diametro = max(diametro, dist[i][j])
    
    return int(diametro)

def calcular_info_grafo(grafo):
    """
    Calcula informações gerais sobre o grafo
    """
    if not grafo:
        return None
        
    # Lista de adjacência para cálculos
    lista_adj = grafo.gerar_lista_adjacencia()
    
    # Calcular graus
    graus = {}
    for v in range(grafo.vertices):
        graus[v] = len(lista_adj[v])
    
    # Calcular distribuição de graus
    distribuicao_graus = {}
    for vertice, grau in graus.items():
        if grau not in distribuicao_graus:
            distribuicao_graus[grau] = {
                'quantidade': 0,
                'vertices': []
            }
        distribuicao_graus[grau]['quantidade'] += 1
        distribuicao_graus[grau]['vertices'].append(mapa_reverso[vertice])
    
    # Ordenar a distribuição por grau
    distribuicao_graus = dict(sorted(distribuicao_graus.items()))
    
    # Encontrar maior e menor grau
    maior_grau = max(graus.values()) if graus else 0
    menor_grau = min(graus.values()) if graus else 0
    
    # Encontrar vértices de maior e menor grau
    vertices_maior_grau = [mapa_reverso[v] for v, g in graus.items() if g == maior_grau]
    vertices_menor_grau = [mapa_reverso[v] for v, g in graus.items() if g == menor_grau]
    
    # Verificar se é conexo usando BFS
    def eh_conexo():
        if grafo.vertices == 0:
            return True
            
        visitados = set()
        fila = [0]
        visitados.add(0)
        
        while fila:
            v = fila.pop(0)
            for u in lista_adj[v]:
                if u not in visitados:
                    visitados.add(u)
                    fila.append(u)
        
        return len(visitados) == grafo.vertices
    
    # Calcular diâmetro
    diametro = calcular_diametro(grafo)
    
    # Encontrar menor ciclo
    menor_ciclo_info = encontrar_menor_ciclo(grafo)
    if menor_ciclo_info:
        menor_ciclo_tamanho, menor_ciclo = menor_ciclo_info
        menor_ciclo_vertices = [mapa_reverso[v] for v in menor_ciclo]
    else:
        menor_ciclo_tamanho, menor_ciclo_vertices = None, None
    
    return {
        'num_vertices': grafo.vertices,
        'num_arestas': len(grafo.arestas),
        'maior_grau': maior_grau,
        'menor_grau': menor_grau,
        'vertices_maior_grau': sorted(vertices_maior_grau),
        'vertices_menor_grau': sorted(vertices_menor_grau),
        'conexo': eh_conexo(),
        'diametro': diametro,
        'menor_ciclo_tamanho': menor_ciclo_tamanho,
        'menor_ciclo_vertices': menor_ciclo_vertices,
        'distribuicao_graus': distribuicao_graus
    }

@app.route("/buscar_ciclo", methods=["POST"])
def buscar_ciclo():
    global grafo_atual
    if not grafo_atual:
        flash("Carregue um grafo primeiro!", "warning")
        return redirect(url_for("index"))
    
    try:
        tamanho = int(request.form.get('tamanho_ciclo', 3))
        if tamanho < 3:
            flash("O tamanho do ciclo deve ser pelo menos 3!", "warning")
            return redirect(url_for("index"))
            
        ciclo = encontrar_ciclo(grafo_atual, tamanho)
        
        if ciclo:
            # Criar nova visualização destacando o ciclo
            net = configurar_network()
            
            # Adicionar todos os nós
            for node_id in range(grafo_atual.vertices):
                nome = mapa_reverso[node_id]
                if node_id in ciclo:
                    # Nós do ciclo em destaque
                    net.add_node(node_id, label=nome, color="#ff7f50", title=nome)
                else:
                    net.add_node(node_id, label=nome, color="#79C2EC", title=nome)
            
            # Adicionar todas as arestas
            for i, (u, v) in enumerate(grafo_atual.arestas):
                if u in ciclo and v in ciclo and abs(ciclo.index(u) - ciclo.index(v)) in [1, len(ciclo)-1]:
                    # Arestas do ciclo em destaque
                    net.add_edge(u, v, color="#ff7f50", width=3)
                else:
                    net.add_edge(u, v, color="#323232")
            
            salvar_visualizacao(net)
            
            # Criar mensagem com os vértices do ciclo
            vertices_ciclo = [mapa_reverso[v] for v in ciclo]
            flash(f"Ciclo de tamanho {tamanho} encontrado: {' -> '.join(vertices_ciclo)}", "success")
        else:
            flash(f"Não foi encontrado nenhum ciclo de tamanho {tamanho}!", "warning")
            
        return redirect(url_for("index"))
        
    except Exception as e:
        flash(f"Erro ao buscar ciclo: {str(e)}", "danger")
        return redirect(url_for("index"))

def encontrar_ciclo(grafo, tamanho):
    """
    Encontra um ciclo de tamanho específico no grafo usando busca em profundidade
    """
    def dfs_ciclo(atual, inicio, caminho, visitados):
        if len(caminho) == tamanho:
            # Verifica se forma um ciclo voltando ao início
            if inicio in grafo.lista_adjacencia[atual]:
                return caminho
            return None
            
        for vizinho in grafo.lista_adjacencia[atual]:
            if vizinho not in visitados:
                novo_caminho = dfs_ciclo(vizinho, inicio, caminho + [vizinho], visitados | {vizinho})
                if novo_caminho:
                    return novo_caminho
        return None
    
    # Gera lista de adjacência se não existir
    if not hasattr(grafo, 'lista_adjacencia'):
        grafo.lista_adjacencia = [[] for _ in range(grafo.vertices)]
        for u, v in grafo.arestas:
            grafo.lista_adjacencia[u].append(v)
            grafo.lista_adjacencia[v].append(u)
    
    # Tenta encontrar ciclo começando de cada vértice
    for v in range(grafo.vertices):
        ciclo = dfs_ciclo(v, v, [v], {v})
        if ciclo:
            return ciclo
            
    return None

def encontrar_menor_ciclo(grafo):
    """
    Encontra o menor ciclo no grafo usando BFS
    Retorna uma tupla (tamanho, ciclo) ou None se não existir ciclo
    """
    if not grafo or grafo.vertices < 3:
        return None

    # Gera lista de adjacência
    lista_adj = grafo.gerar_lista_adjacencia()

    menor_ciclo = None
    menor_tamanho = float('inf')

    # Para cada vértice como ponto inicial
    for inicio in range(grafo.vertices):
        # BFS
        visitados = [-1] * grafo.vertices
        pai = [-1] * grafo.vertices
        fila = [(inicio, -1)]  # (vértice, pai)
        
        visitados[inicio] = 0
        
        while fila:
            v, p = fila.pop(0)
            
            for vizinho in lista_adj[v]:
                if visitados[vizinho] == -1:  # Não visitado
                    visitados[vizinho] = visitados[v] + 1
                    pai[vizinho] = v
                    fila.append((vizinho, v))
                elif vizinho != p and vizinho != inicio:  # Encontrou ciclo
                    # Reconstruir o ciclo
                    ciclo = [v]
                    atual = v
                    while atual != inicio:
                        atual = pai[atual]
                        ciclo.append(atual)
                    ciclo.reverse()
                    
                    tamanho = len(ciclo)
                    if tamanho < menor_tamanho:
                        menor_tamanho = tamanho
                        menor_ciclo = ciclo

    return (menor_tamanho, menor_ciclo) if menor_ciclo else None

# Configuração para o Render
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
