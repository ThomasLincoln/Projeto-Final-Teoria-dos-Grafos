# grafo.py

import networkx as nx
import matplotlib.pyplot as plt
import itertools

class Grafo:
    def __init__(self, vertices=None):
        self.vertices = vertices if vertices is not None else 0
        self.arestas = []

    def adicionar_aresta(self, u, v):
        if u < self.vertices and v < self.vertices:
            if (v, u) not in self.arestas and (u, v) not in self.arestas:
                self.arestas.append((u, v))
        else:
            print("Vértice inválido")

    def gerar_matriz_adjacencia(self):
        matriz = [[0 for _ in range(self.vertices)] for _ in range(self.vertices)]
        for u, v in self.arestas:
            matriz[u][v] = 1
            matriz[v][u] = 1
        return matriz

    def mostrar_matriz_adjacencia(self):
        matriz = self.gerar_matriz_adjacencia()
        for linha in matriz:
            print(linha)

    def gerar_matriz_incidencia(self):
        matriz = [[0 for _ in range(len(self.arestas))] for _ in range(self.vertices)]
        for idx, (u, v) in enumerate(self.arestas):
            matriz[u][idx] = 1
            matriz[v][idx] = 1
        return matriz

    def mostrar_matriz_incidencia(self):
        matriz = self.gerar_matriz_incidencia()
        for linha in matriz:
            print(linha)

    @staticmethod
    def gerar_grafo_de_matriz_adjacencia(matriz):
        vertices = len(matriz)
        novo_grafo = Grafo(vertices)
        for i in range(vertices):
            for j in range(i + 1, vertices):
                if matriz[i][j] == 1:
                    novo_grafo.adicionar_aresta(i, j)
        return novo_grafo

    @staticmethod
    def gerar_grafo_de_matriz_incidencia(matriz):
        vertices = len(matriz)
        arestas = len(matriz[0]) if vertices > 0 else 0
        grafo = Grafo(vertices)
        for j in range(arestas):
            u = -1
            v = -1
            for i in range(vertices):
                if matriz[i][j] == 1:
                    if u == -1:
                        u = i
                    else:
                        v = i
                        break
            if u != -1 and v != -1:
                grafo.adicionar_aresta(u, v)
        return grafo

    @staticmethod
    def gerar_grafo_de_lista_adjacencia(lista_adjacencia):
        vertices = len(lista_adjacencia)
        grafo = Grafo(vertices)
        for u, adjacentes in lista_adjacencia.items():
            for v in adjacentes:
                grafo.adicionar_aresta(u, v)
        return grafo

    def mostrar_grafo(self):
        for u, v in self.arestas:
            print(f"{u} -> {v}")

    def visualizar_grafo(self):
        G = nx.Graph()
        G.add_edges_from(self.arestas)
        nx.draw(G, with_labels=True, node_color='lightblue', node_size=500, font_size=10, font_weight='bold')
        plt.show()

    def gerar_lista_adjacencia(self):
        lista_adj = {i: [] for i in range(self.vertices)}
        for u, v in self.arestas:
            lista_adj[u].append(v)
            lista_adj[v].append(u)
        return lista_adj

    def mostrar_lista_adjacencia(self):
        lista_adjacencia = self.gerar_lista_adjacencia()
        for vertice, adjacentes in lista_adjacencia.items():
            print(f"{vertice}: {', '.join(map(str, adjacentes))}")

    @staticmethod
    def gerar_grafo_completo(vertices):
        grafo = Grafo(vertices)
        for i in range(vertices):
            for j in range(i + 1, vertices):
                grafo.adicionar_aresta(i, j)
        return grafo

    def sao_isomorfos(self, outro_grafo):
        if self.vertices != outro_grafo.vertices or len(self.arestas) != len(outro_grafo.arestas):
            return False
        
        lista1 = self.gerar_lista_adjacencia()
        lista2 = outro_grafo.gerar_lista_adjacencia()
        
        for permutacao in itertools.permutations(range(self.vertices)):
            isomorfico = True
            for vertice in range(self.vertices):
                adjacentes1 = set(lista1[vertice])
                adjacentes2 = set(permutacao[v] for v in lista2[permutacao[vertice]])
                if adjacentes1 != adjacentes2:
                    isomorfico = False
                    break
            if isomorfico:
                return True
        return False

    def uniao(self, outro_grafo):
        total_vertices = max(self.vertices, outro_grafo.vertices)
        matriz_self = self.gerar_matriz_adjacencia()
        matriz_outro = outro_grafo.gerar_matriz_adjacencia()

        # Ajusta (expande) a menor matriz
        if self.vertices < total_vertices:
            for linha in matriz_self:
                linha.extend([0] * (total_vertices - self.vertices))
            for _ in range(total_vertices - self.vertices):
                matriz_self.append([0] * total_vertices)

        if outro_grafo.vertices < total_vertices:
            for linha in matriz_outro:
                linha.extend([0] * (total_vertices - outro_grafo.vertices))
            for _ in range(total_vertices - outro_grafo.vertices):
                matriz_outro.append([0] * total_vertices)

        matriz_uniao = []
        for i in range(total_vertices):
            linha_uniao = []
            for j in range(total_vertices):
                if matriz_self[i][j] == 1 or matriz_outro[i][j] == 1:
                    linha_uniao.append(1)
                else:
                    linha_uniao.append(0)
            matriz_uniao.append(linha_uniao)

        grafo_uniao = Grafo.gerar_grafo_de_matriz_adjacencia(matriz_uniao)
        return grafo_uniao

    def interseccao(self, outro_grafo):
        min_vertices = min(self.vertices, outro_grafo.vertices)
        matriz_self = self.gerar_matriz_adjacencia()
        matriz_outro = outro_grafo.gerar_matriz_adjacencia()
        grafo_intersecao = Grafo(min_vertices)
        for i in range(min_vertices):
            for j in range(i + 1, min_vertices):
                if matriz_self[i][j] == 1 and matriz_outro[i][j] == 1:
                    grafo_intersecao.adicionar_aresta(i, j)
        return grafo_intersecao

    def diferenca_simetrica(self, outro_grafo):
        grafo_diff_sim = Grafo(max(self.vertices, outro_grafo.vertices))
        grafo_diff_sim.arestas = list(set(self.arestas) ^ set(outro_grafo.arestas))
        return grafo_diff_sim

    def remover_vertice(self, vertice):
        if vertice < self.vertices:
            novo_grafo = Grafo(self.vertices - 1)
            novo_grafo.arestas = [(u, v) for u, v in self.arestas if u != vertice and v != vertice]
            return novo_grafo
        else:
            print("Vértice não encontrado.")
            return self

    def remover_aresta(self, aresta):
        if aresta in self.arestas:
            novo_grafo = Grafo(self.vertices)
            novo_grafo.arestas = [a for a in self.arestas if a != aresta]
            return novo_grafo
        else:
            print("Aresta não encontrada.")
            return self

    def fundir_vertices(self, v1, v2):
        if v1 < self.vertices and v2 < self.vertices:
            novas_arestas = set()
            for u, v in self.arestas:
                if u == v2:
                    u = v1
                if v == v2:
                    v = v1
                if u != v or v != u:
                    novas_arestas.add((min(u, v), max(u, v)))
            self.arestas = list(novas_arestas)
        else:
            print("Um ou ambos os vértices não foram encontrados.")

    def is_arvore(self):
        if len(self.arestas) != self.vertices - 1:
            return False
        return self.is_conexo()

    def is_conexo(self):
        if not self.vertices:
            return True
        
        visitados = set()
        def dfs(v):
            visitados.add(v)
            for u, w in self.arestas:
                if u == v and w not in visitados:
                    dfs(w)
                elif w == v and u not in visitados:
                    dfs(u)
        
        dfs(0)  # começa do vértice 0
        return len(visitados) == self.vertices

    def is_subgrafo_de(self, G):
        if self.vertices > G.vertices:
            return False
        for u, v in self.arestas:
            if (u, v) not in G.arestas and (v, u) not in G.arestas:
                return False
        return True

    def is_arvore_abrangencia_de(self, G):
        if not self.is_arvore():
            return False
        if self.vertices != G.vertices:
            return False
        return self.is_subgrafo_de(G)

    def is_euleriano(self):
        # Verifica se o grafo é conexo
        if not self.is_conexo():
            return False, "O grafo não é conexo"
        
        # Gera lista de adjacência para contar graus
        lista_adj = self.gerar_lista_adjacencia()
        
        # Conta vértices com grau ímpar
        vertices_impares = sum(1 for v in lista_adj.values() if len(v) % 2 != 0)
        
        # Um grafo é euleriano se todos os vértices têm grau par
        if vertices_impares == 0:
            return True, "O grafo é euleriano"
        # Um grafo é semi-euleriano se exatamente dois vértices têm grau ímpar
        elif vertices_impares == 2:
            return False, "O grafo é semi-euleriano (possui caminho euleriano)"
        else:
            return False, "O grafo não é euleriano nem semi-euleriano"

    def is_hamiltoniano(self):
        if self.vertices < 3:
            return False, "O grafo precisa ter pelo menos 3 vértices para ser hamiltoniano"
        
        def tem_ciclo_hamiltoniano(grafo, pos, caminho, visitados, inicio):
            # Se todos os vértices foram visitados e podemos voltar ao início
            if len(caminho) == grafo.vertices and caminho[0] in grafo.get_vizinhos(caminho[-1]):
                return True
            
            # Tenta adicionar cada vértice adjacente não visitado ao caminho
            for v in grafo.get_vizinhos(pos):
                if v not in visitados:
                    visitados.add(v)
                    caminho.append(v)
                    if tem_ciclo_hamiltoniano(grafo, v, caminho, visitados, inicio):
                        return True
                    visitados.remove(v)
                    caminho.pop()
            return False
        
        def get_vizinhos(self, vertice):
            vizinhos = []
            for u, v in self.arestas:
                if u == vertice:
                    vizinhos.append(v)
                elif v == vertice:
                    vizinhos.append(u)
            return vizinhos
        
        # Adiciona o método get_vizinhos temporariamente à instância
        self.get_vizinhos = lambda v: get_vizinhos(self, v)
        
        # Tenta encontrar um ciclo hamiltoniano começando de cada vértice
        for inicio in range(self.vertices):
            caminho = [inicio]
            visitados = {inicio}
            if tem_ciclo_hamiltoniano(self, inicio, caminho, visitados, inicio):
                return True, "O grafo é hamiltoniano (possui um ciclo hamiltoniano)"
        
        # Remove o método temporário
        delattr(self, 'get_vizinhos')
        
        return False, "O grafo não é hamiltoniano"

    def encontrar_corte_fundamental(self):
        if not self.is_conexo():
            return None, "O grafo não é conexo"
        
        if not self.arestas:
            return None, "O grafo não possui arestas"
        
        # Criar grafo NetworkX
        G = nx.Graph()
        G.add_edges_from(self.arestas)
        
        # Obter árvore geradora mínima
        T = nx.minimum_spanning_tree(G)
        
        # Escolher uma aresta da árvore
        aresta_escolhida = list(T.edges())[0]
        
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
            
            return corte_fundamental, f"Corte fundamental encontrado com {len(corte_fundamental)} arestas"
            
        except Exception as e:
            return None, f"Erro ao encontrar corte fundamental: {str(e)}"
