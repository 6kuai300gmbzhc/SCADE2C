# 单向图，支持查询到节点的边和节点出发的边
from collections import deque


class Vertex:
    def __init__(self, value):
        self.value = value
        self.connectedTo = {}
        self.connectedFrom = {}
        self.connectedFromAllSet = set()

    def add_to(self, nbr, arrow=0):
        self.connectedTo[nbr] = arrow

    def add_from(self, nbr, arrow=0):
        # 把from的节点的依赖节点集合合并进来,再加上自己
        self.connectedFrom[nbr] = arrow
        self.update_connectedFromAll(nbr)

    def update_connectedFromAll(self, vertex):
        """把目标节点的集合合并到自己身上,并递归的更新自己所连接到的其他节点"""
        checked_set = set()
        stack = deque([self])
        while stack:
            tar_vertex = stack.pop()
            if tar_vertex in checked_set: continue
            tar_vertex.connectedFromAllSet |= vertex.connectedFromAllSet
            tar_vertex.connectedFromAllSet.add(vertex)
            checked_set.add(tar_vertex)
            for nxt_vertex in tar_vertex.get_to_vertexes():
                stack.append(nxt_vertex)

    def __str__(self):
        return str(self.value) + \
               ' 连接到: ' + str([x.value for x in self.connectedTo]) + \
               ' 来自: ' + str([x.value for x in self.connectedFrom])

    def get_to_vertexes(self):
        return self.connectedTo.keys()

    def get_from_vertexes(self):
        return self.connectedFrom.keys()

    def getValue(self):
        return self.value

    def get_to_connection(self, nbr):
        return self.connectedTo[nbr]

    def get_from_connection(self, nbr):
        return self.connectedFrom[nbr]

    def get_all_from_vertexes(self) -> set:
        return self.connectedFromAllSet


class Graph:
    def __init__(self):
        self.vertList = {}
        self.numVertices = 0

    def addVertex(self, key) -> Vertex:
        if key in self.vertList.keys():
            return self.getVertex(key)
        self.numVertices = self.numVertices + 1
        newVertex = Vertex(key)
        self.vertList[key] = newVertex
        return newVertex

    def getVertex(self, key):
        return self.vertList.get(key)

    def get_all_from_vertexes_from_value(self, value) -> list or None:
        """找到连接到有此值的节点的其他所有节点"""
        src_vertex = self.getVertex(value)
        if not src_vertex: return None
        return src_vertex.get_all_from_vertexes()

    def __contains__(self, n):
        return n in self.vertList

    def addEdge(self, from_vertex, to_vertex, arrow=0):
        # 在添加边的时候，也需要更新to_vertex，更新所有可以到它的节点列表
        if from_vertex not in self.vertList:
            self.addVertex(from_vertex)
        if to_vertex not in self.vertList:
            self.addVertex(to_vertex)
        self.vertList[from_vertex].add_to(self.vertList[to_vertex], arrow)
        self.vertList[to_vertex].add_from(self.vertList[from_vertex], arrow)

    def getVertices(self):
        return self.vertList.values()

    def __iter__(self):
        return iter(self.vertList.values())

    def __repr__(self):
        out = ""
        for v in self:
            out += "TO:"
            for w in v.get_to_vertexes():
                out += f"({v.getValue()} , {w.getValue()})"
            out += "FROM:"
            for f in v.get_from_vertexes():
                out += f"({v.getValue()} , {f.getValue()})"
        return out

    def topological_sort(self) -> list or None:
        """进行拓扑排序，返回排序之后的数组,若无法排序则返回None"""
        # 计算每个节点的入度
        # key就是value，value就是key
        in_degree = {key: 0 for key in self.vertList}
        for vertex in self.vertList.values():
            for to_vertex in vertex.get_to_vertexes():
                in_degree[to_vertex.value] += 1

        # 将所有入度为 0 的节点加入队列
        queue = deque([key for key in self.vertList if in_degree[key] == 0])
        topo_order = []
        while queue:
            current = queue.popleft()
            topo_order.append(current)
            for to_vertex in self.vertList[current].get_to_vertexes():
                in_degree[to_vertex.value] -= 1
                if in_degree[to_vertex.value] == 0:
                    queue.append(to_vertex.value)

        if len(topo_order) != self.numVertices:
            return None
        return topo_order


if __name__ == "__main__":
    # 实例化
    g = Graph()
    for i in range(6):
        g.addVertex(i)
    # print(g.vertList)
    g.addEdge(0, 1, 5)
    g.addEdge(0, 5, 2)
    g.addEdge(1, 2, 4)
    g.addEdge(2, 3, 9)
    g.addEdge(3, 4, 7)
    # g.addEdge(3, 5, 3)
    # g.addEdge(4, 0, 1)
    g.addEdge(5, 4, 8)
    g.addEdge(5, 2, 1)
    for v in g:
        print()
        print(v.value)
        print("TO")
        for w in v.get_to_vertexes():
            print("(%s , %s)" % (v.getValue(), w.getValue()))
        print("FROM")
        for f in v.get_from_vertexes():
            print("(%s , %s)" % (f.getValue(), v.getValue()))
        print("FIN")
        print([t.value for t in v.connectedFromAllSet])
