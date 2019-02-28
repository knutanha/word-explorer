import anytree as tree
import pandas as pd
import random
import matplotlib.pyplot as plt
from scipy.stats import truncnorm
import itertools
import name_creator as nc
import numpy as np


class OrgUnit:
    def __init__(self, id: int, name: str) -> None:
        self.id = id
        self.name = name

    def __repr__(self) -> str:
        return f'OrgUnit[{self.id}]<"{self.get_name()}">'

    def __str__(self) -> str:
        return self.__repr__()

    def get_name(self):
        return self.name


class OrgUnitNameCreator:
    def __init__(self) -> None:
        base_path = r'C:\Dev\Python\word-explorer\word-explorer\resources'
        self.word_classes = ['adjective', 'adverb', 'noun', 'verb']
        self.words = dict()
        for word_class in self.word_classes:
            self.words[word_class] = pd.read_csv(f'{base_path}\\{word_class}s.txt')

        self.structure = [
            ['noun'],
            ['adjective', 'parent'],
            ['parent', '- verb'],
            ['parent-3', '(adverb)'],
            ['parent-3', '(adverb', 'verb)'],
            # ['parent-3', '(adverb', 'verb)', '- depth'],
        ]

    def generate_name(self, parent: tree.Node = None):
        if parent:
            structure = self.structure[min(parent.depth, len(self.structure) - 1)]
            name_components = []
            for i in structure:
                if 'parent' in i:
                    comp = i.split('-')
                    target = parent
                    if len(comp) > 1:
                        for ancestor in parent.ancestors:
                            if ancestor.depth == int(comp[-1]):
                                target = ancestor
                                break
                    name_components.append(target.name.name)
                else:
                    for word_class in self.word_classes + ['depth']:
                        if word_class in i:
                            split = i.split(word_class, maxsplit=1)
                            if 'depth' in i:
                                name = str(parent.depth - len(self.structure) + 1)
                            else:
                                name = str.capitalize(
                                    str(
                                        self.words[word_class].sample().values[0][0]
                                    )
                                )
                            name_components.append(name if len(split) == 0 else name.join(split))
                            break

            return ' '.join(name_components)
        else:
            return 'root',


class Employee:
    __name_generator = nc.generate_names()
    __id_generator = itertools.count(0)

    def __init__(self, id: int = None, name_components: int = None) -> None:
        if not name_components:
            name_components = next(self.__name_generator)
        self.__name_components = name_components
        if not id:
            id = next(self.__id_generator)
        self.__id = id

    def __repr__(self) -> str:
        return f'Employee[{self.__id}]<{self.__name_components[0]} {self.__name_components[1]} ({self.__name_components[2]})>'


def org_unit_tree_creator(n, a, b):
    creator = OrgUnitNameCreator()
    root = tree.Node(OrgUnit(0, creator.generate_name()))
    leaf_nodes = [root]
    ou_id = 1
    while n > 0:
        # select random leaf node
        # TODO: Tends to pick from large clusters
        selection = 0
        if len(leaf_nodes) > 1:
            dist = get_truncated_normal(2, sd=b//2, low=0, upp=len(leaf_nodes)-1)  # Selects the closest
            # next_parent_node = leaf_nodes.pop(random.randint(0, len(leaf_nodes) - 1))
            selection = int(dist.rvs(1)[0])
        next_parent_node = leaf_nodes.pop(selection)

        # select number of new divisions
        number_of_divisions = min(random.randint(a, b) if next_parent_node.depth > 0 else b, n)
        for i in range(number_of_divisions):
            leaf_nodes.append(
                tree.Node(
                    OrgUnit(
                        ou_id,
                        creator.generate_name(next_parent_node)
                    ),
                    parent=next_parent_node)
            )
            ou_id += 1
        n -= number_of_divisions
    return root


def print_tree(root: tree.Node):
    for pre, fill, node in tree.RenderTree(root):
        print("%s%s" % (pre, node.name))


def populate_tree_with_employees(n: int, root: tree.Node, node_min: int, node_max: int):
    # TODO: Make sure that number of employees is at least as large as the number of org units
    top_nodes = root.children
    # distribute total number of employees in each top node
    population_dist = np.array(distribute_over_objects(n, top_nodes), dtype=np.int)

    # order so the top nodes with the most descendants has the most employees
    desc_dist = np.array([len(i.descendants) for i in top_nodes], dtype=np.int)
    arg_sort_desc_dist = list(np.argsort(desc_dist))
    population_dist.sort()
    population_dist_reordered = np.zeros(len(desc_dist), dtype=np.int)
    for i in range(len(desc_dist)):
        population_dist_reordered[i] = population_dist[arg_sort_desc_dist.index(i)]

    # print('desc_dist                ', desc_dist)
    # print('population_dist          ', population_dist)
    # print('arg_sort_desc_dist       ', arg_sort_desc_dist)
    # print('population_dist_reordered', population_dist_reordered)

    # [print(top_nodes[i].name.get_name(), population_dist[i]) for i in range(len(top_nodes))]
    # distribute employees to children of top_nodes
    # leaves first
    for i, top_node in enumerate(top_nodes):
        pop = population_dist_reordered[i]
        # print('descendants', top_node.descendants)
        candidates = top_node.descendants
        if len(candidates) == 0:
            candidates = [top_node]
        pop_dist = distribute_over_objects(pop, candidates)
        for j, candidate in enumerate(candidates):
            for _ in range(pop_dist[j]):
                tree.Node(Employee(), parent=candidate)


def get_truncated_normal(mean=0, sd=1, low=0, upp=10):
    return truncnorm(
        (low - mean) / sd, (upp - mean) / sd, loc=mean, scale=sd)


def distribute_over_objects(n: int, objects: list, mean=8, sd=20, low=1, upp=30):
    dist = get_truncated_normal(mean, sd=sd, low=low, upp=upp)
    result = dist.rvs(len(objects))
    s = sum(result)
    population_dist = [int(i / s * n) for i in result]
    s2 = sum(population_dist)
    # TODO: Make sure all nodes has at least one? Alt: Only for leaf nodes
    while s2 < n:
        sort_index = np.argsort(population_dist)
        if population_dist[sort_index[0]] == 0:
            population_dist[sort_index[0]] += 1
            s2 += 1
        else:
            for i in range(n - s2):
                population_dist[-i - 1] += 1
                s2 += 1
    return population_dist


if __name__ == '__main__':
    a = org_unit_tree_creator(100, 1, 8)
    top_descendant_len = [len(i.descendants) for i in a.children]
    print_tree(a)

    populate_tree_with_employees(1000, a, 0, 1)
    #print_tree(a)

    [print(i.name, 'deps=', top_descendant_len[k], 'emps=', len([j for j in i.descendants if isinstance(j.name, Employee)])) for k, i in enumerate(a.children)]

    # fig, ax = plt.subplots(1)
    # ax.hist(x.rvs(10000), normed=True)
    # plt.show()
