# classes/b_tree.py
import graphviz # Asegúrate de que Graphviz esté instalado en tu sistema y en PATH

class BTreeNode:
    def __init__(self, t, is_leaf):
        self.t = t  # Grado mínimo (orden del árbol)
        self.is_leaf = is_leaf  # Booleano: ¿Es un nodo hoja?
        self.keys = []  # Lista de claves en este nodo
        self.children = []  # Lista de nodos hijos (punteros a otros nodos)
        self.n = 0  # Número actual de claves en el nodo

    def __repr__(self):
        return f"Node(keys={self.keys}, leaf={self.is_leaf})"

class BTree:
    def __init__(self, order):
        self.order = order  # Corresponde a 't' en la teoría de B-trees
        self.root = BTreeNode(order, True)  # La raíz es inicialmente una hoja
        self.next_id_counter = 1 # Para generar IDs únicos si se necesita

    def search(self, key):
        return self._search(self.root, key)

    def _search(self, x, key):
        i = 0
        while i < x.n and key > x.keys[i].id:
            i += 1
        if i < x.n and key == x.keys[i].id:
            return x.keys[i]  # Se encontró la clave (el objeto Place)
        if x.is_leaf:
            return None  # No se encontró y es una hoja
        return self._search(x.children[i], key) # Busca en el hijo apropiado

    def insert(self, key_id, value):
        root_node = self.root
        # Si la raíz está llena, el árbol crece en altura
        if root_node.n == (2 * self.order) - 1:
            s = BTreeNode(self.order, False) # Nueva raíz no hoja
            s.children.insert(0, root_node) # La vieja raíz es ahora el primer hijo de la nueva raíz
            self._split_child(s, 0) # Divide la vieja raíz
            self.root = s # La nueva raíz es ahora la raíz del árbol
        self._insert_non_full(self.root, key_id, value)

    def _insert_non_full(self, x, key_id, value):
        i = x.n - 1
        if x.is_leaf:
            # Encuentra la posición correcta para insertar la clave
            while i >= 0 and key_id < x.keys[i].id:
                i -= 1
            x.keys.insert(i + 1, value) # Inserta el objeto Place
            x.n += 1
        else:
            # Encuentra el hijo donde se debería insertar
            while i >= 0 and key_id < x.keys[i].id:
                i -= 1
            i += 1 # i es el índice del hijo donde se insertará

            # Si el hijo está lleno, divídelo
            if x.children[i].n == (2 * self.order) - 1:
                self._split_child(x, i)
                # Decide en qué hijo continuar la inserción después de la división
                if key_id > x.keys[i].id:
                    i += 1
            self._insert_non_full(x.children[i], key_id, value)

    def _split_child(self, x, i):
        t = self.order
        y = x.children[i] # y es el hijo que está lleno
        z = BTreeNode(t, y.is_leaf) # z es el nuevo nodo que se creará
        
        x.keys.insert(i, y.keys[t - 1]) # Sube la clave mediana de y a x
        x.n += 1

        z.n = t - 1 # El nuevo nodo z toma t-1 claves
        y.n = t - 1 # El nodo y se queda con t-1 claves

        # Copia las claves de la mitad derecha de y a z
        z.keys = y.keys[t : (2 * t) - 1]
        y.keys = y.keys[0 : t - 1]

        if not y.is_leaf:
            # Si y no es una hoja, z también toma la mitad derecha de los hijos de y
            z.children = y.children[t : (2 * t)]
            y.children = y.children[0 : t]
        
        x.children.insert(i + 1, z) # Inserta z como un nuevo hijo de x

    def get_all_elements(self):
        """Devuelve una lista de todos los elementos (Place objects) en el árbol, en orden."""
        elements = []
        self._traverse_and_collect(self.root, elements)
        return elements

    def _traverse_and_collect(self, node, elements):
        if not node:
            return

        # Recorre los hijos y las claves
        for i in range(node.n):
            if not node.is_leaf:
                self._traverse_and_collect(node.children[i], elements)
            elements.append(node.keys[i]) # Las claves son los objetos Place

        # Asegúrate de recorrer el último hijo si no es una hoja
        if not node.is_leaf:
            self._traverse_and_collect(node.children[node.n], elements)
    
    def to_dot(self):
        """Genera una representación DOT del árbol para Graphviz."""
        dot = graphviz.Digraph(comment='B-Tree Structure', graph_attr={'rankdir': 'TB', 'splines': 'true'})
        node_counter = [0] # Usar una lista para mutabilidad

        def add_nodes_edges(node, parent_name=None, child_idx=None):
            current_node_name = f'node{node_counter[0]}'
            node_counter[0] += 1
            
            # Crear la etiqueta del nodo
            label = '|'.join([f'<p{j}>' for j in range(node.n)] + 
                             [str(key.id) for key in node.keys] +
                             [f'<p{j}>' for j in range(node.n, 2 * self.order - 1)])
            
            # Simplificar la etiqueta para mostrar solo las claves
            label_keys = '|'.join([str(key.id) for key in node.keys])
            dot.node(current_node_name, label=f"{{ {label_keys} }}", shape='record')

            if parent_name:
                # Conectar el nodo padre con este nodo hijo
                # Si queremos conectar a un puerto específico del padre:
                dot.edge(f'{parent_name}:p{child_idx}', current_node_name)

            if not node.is_leaf:
                for i, child in enumerate(node.children):
                    if child: # Asegurarse de que el hijo no sea None
                        add_nodes_edges(child, current_node_name, i)
        
        if self.root:
            add_nodes_edges(self.root)
        return dot.source