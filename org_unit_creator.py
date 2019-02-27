import anytree as tree
import pandas as pd
import random


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

        self.structure = [['noun'], ['adjective', 'parent'], ['parent', 'verb'], ['adverb', 'parent'],
                          ['parent-4', '(adjective)']]

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
                    for word_class in self.word_classes:
                        if word_class in i:
                            split = i.split(word_class, maxsplit=1)
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


def org_unit_tree_creator(n, a, b):
    creator = OrgUnitNameCreator()
    root = tree.Node(OrgUnit(0, creator.generate_name()))
    leaf_nodes = [root]
    ou_id = 1
    while n > 0:
        # select number of new divisions
        number_of_divisions = min(random.randint(a, b), n)

        # select random leaf node
        next_parent_node = leaf_nodes.pop(random.randint(0, len(leaf_nodes) - 1))
        for i in range(number_of_divisions):
            leaf_nodes.append(
                tree.Node(OrgUnit(ou_id, creator.generate_name(next_parent_node)), parent=next_parent_node))
            ou_id += 1
        n -= number_of_divisions
    return root


def print_tree(root: tree.Node):
    for pre, fill, node in tree.RenderTree(root):
        print("%s%s" % (pre, node.name))

def populate_tree_with_employees():
    pass

a = org_unit_tree_creator(25, 3, 8)
print_tree(a)
print(a.leaves)

