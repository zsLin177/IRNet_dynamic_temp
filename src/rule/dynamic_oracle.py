# 用来在使用dynamic oracle进行训练的时候，
# 根据当前已经生成的action序列（partical AST tree）和current objective，
# 来生成新的objective

from src.rule.lf import build_tree, build_sketch_tree
from src.rule.semQL import Sup, Sel, Order, Root, Filter, A, N, C, T, Root1
import random

Keywords = ['des', 'asc', 'and', 'or', 'sum', 'min', 'max', 'avg', 'none', '=', '!=', '<', '>', '<=', '>=', 'between', 'like', 'not_like'] + [
    'in', 'not_in', 'count', 'intersect', 'union', 'except'
]


def preorder_travel_all(node, lst):
    lst.append(node)
    for child in node.children:
        preorder_travel_all(child, lst)
    return lst


def generate(node, selected_C):
    if(isinstance(node, A)):
        idx = random.randint(0, len(selected_C)-1)
        selected_C[idx].set_parent(node)
        node.add_children(selected_C[idx])
        return
    elif(isinstance(node, Root1)):
        child = Root(5)
        child.set_parent(node)
        node.add_children(child)
        generate(child, selected_C)
    elif(isinstance(node, Root)):
        child = Sel(0)
        child.set_parent(node)
        node.add_children(child)
        generate(child, selected_C)
    elif(isinstance(node, Sel)):
        child = N(0)
        child.set_parent(node)
        node.add_children(child)
        generate(child, selected_C)
    elif(isinstance(node, N) or isinstance(node, Order) or isinstance(node, Sup) or isinstance(node, Filter)):
        child = A(0)
        child.set_parent(node)
        node.add_children(child)
        generate(child, selected_C)


def generate_sketch(node):
    if (isinstance(node, N) or isinstance(node, Order) or isinstance(node, Sup) or isinstance(node, Filter)):
        return
    elif (isinstance(node, Root1)):
        child = Root(5)
        child.set_parent(node)
        node.add_children(child)
        generate_sketch(child)
    elif (isinstance(node, Root)):
        child = Sel(0)
        child.set_parent(node)
        node.add_children(child)
        generate_sketch(child)
    elif (isinstance(node, Sel)):
        child = N(0)
        child.set_parent(node)
        node.add_children(child)
        generate_sketch(child)


def derive_sketch(nodes_type):
    lst = []
    for node_type in nodes_type:
        if (node_type == Root1):
            node = Root1(3)
        elif (node_type == Root):
            node = Root(5)
        elif (node_type == N):
            node = N(0)  # 此处存疑，或许也可以是包含selected_A中所有的A
        elif (node_type == Sel):
            node = Sel(0)
        elif (node_type == Filter):
            id = random.randint(2, 10)
            node = Filter(id)
        elif (node_type == Order):
            id = random.randint(0, 1)
            node = Order(id)
        elif (node_type == Sup):
            id = random.randint(0, 1)
            node = Sup(id)

        generate_sketch(node)
        lst.append(node)
    return lst


def derive(nodes_type, selected_C):
    lst = []
    for node_type in nodes_type:
        if(node_type == Root1):
            node = Root1(3)
        elif(node_type == Root):
            node = Root(5)
        elif(node_type == N):
            node = N(0)  # 此处存疑，或许也可以是包含selected_A中所有的A
        elif(node_type == A):
            node = A(0)
        elif(node_type == Sel):
            node = Sel(0)
        elif(node_type == Filter):
            id = random.randint(2, 10)
            node = Filter(id)
        elif(node_type == Order):
            id = random.randint(0, 1)
            node = Order(id)
        elif(node_type == Sup):
            id = random.randint(0, 1)
            node = Sup(id)

        generate(node, selected_C)
        lst.append(node)
    return lst


def adjust(action_seq, current_obj):
    '''
    action_seq:目前模型已经生成的action序列,类型不是字符串
    current_obj:当前的object action序列，类型不是字符串
    return:新的object action序列
    # current_obj需要调整的也就是把action_o为根的子树换成以action_p为根的子树
    '''

    if(action_seq[-1] == current_obj[len(action_seq)-1]):
        return current_obj

    already_correct = action_seq[0:-1]
    action_p = action_seq[-1]
    # action_o = current_obj[len(already_correct)]
    current_obj_tree = build_tree(current_obj)  # 建成了树的结构
    node_lst = []
    preorder_travel_all(current_obj_tree, node_lst)

    selected_C = []
    for node in node_lst:
        if(isinstance(node, C)):
            selected_C.append(node)

    node_o = node_lst[len(already_correct)]
    p_children = action_p.get_next_action()
    o_children = node_o.children
    p_plus_children_type = []
    for p_child in p_children:
        flag = 0
        for i in range(len(o_children)-1, -1, -1):
            if(isinstance(o_children[i], p_child)):
                o_children[i].set_parent(action_p)
                action_p.add_children(o_children[i])
                o_children.pop(i)
                flag = 1
                break
        if(flag == 0):
            p_plus_children_type.append(p_child)

    new_children = derive(p_plus_children_type, selected_C)
    for new_child in new_children:
        new_child.set_parent(action_p)
        action_p.add_children(new_child)

    parent = node_o.parent
    parent.children.remove(node_o)
    action_p.set_parent(parent)
    parent.add_children(action_p)

    new_node_lst = []
    preorder_travel_all(current_obj_tree, new_node_lst)
    # print(new_node_lst)

    return new_node_lst
    # print(new_node_lst)
    # print(action_p)


def adjust_sketch(action_seq, current_obj):
    '''
    action_seq:目前模型已经生成的action序列,类型不是字符串
    current_obj:当前的object action序列，类型不是字符串
    return:新的object action序列
    # current_obj需要调整的也就是把action_o为根的子树换成以action_p为根的子树
    '''
    idx = 0
    flag = 0
    for idx in range(len(action_seq)):
        if(action_seq[idx] != current_obj[idx]):
            flag = 1
            break

    if(flag == 0):
        return current_obj

    action_p = action_seq[idx]
    # action_o = current_obj[len(already_correct)]
    current_obj_tree = build_sketch_tree(current_obj)  # 建成了树的结构
    node_lst = []
    preorder_travel_all(current_obj_tree, node_lst)

    # selected_C = []
    # for node in node_lst:
    #     if(isinstance(node,C)):
    #         selected_C.append(node)

    node_o = node_lst[idx]
    p_children = action_p.get_next_action()
    o_children = node_o.children
    p_plus_children_type = []
    for p_child in p_children:
        if(p_child == C or p_child == T or p_child == A):
            continue

        flag = 0
        for i in range(len(o_children)-1, -1, -1):
            if(isinstance(o_children[i], p_child)):
                o_children[i].set_parent(action_p)
                action_p.add_children(o_children[i])
                o_children.pop(i)
                flag = 1
                break
        if(flag == 0):
            p_plus_children_type.append(p_child)

    new_children = derive_sketch(p_plus_children_type)
    for new_child in new_children:
        new_child.set_parent(action_p)
        action_p.add_children(new_child)

    parent = node_o.parent
    if(parent):
        parent.children.remove(node_o)
        action_p.set_parent(parent)
        parent.add_children(action_p)

        new_node_lst = []
        preorder_travel_all(current_obj_tree, new_node_lst)
        # print(new_node_lst)
        for node in new_node_lst:
            node.parent = None
            node.children = []

        return new_node_lst
    else:
        new_node_lst = []
        preorder_travel_all(action_p, new_node_lst)

        for node in new_node_lst:
            node.parent = None
            node.children = []

        return new_node_lst

    # print(new_node_lst)
    # print(action_p)


if __name__ == '__main__':
    # correct_s = "Root1(3) Root(4) Sel(0) N(2) A(0) C(3) T(1) A(0) C(9) T(1) A(0) C(12) T(1) Order(0) A(0) C(12) T(1)".split()
    correct = [Root1(3), Root(3), Sel(0), N(0), Filter(0), Filter(
        0), Filter(2), Root(3), Sel(0), N(0), Filter(2), Filter(2)]
    # predicted_s = 'Root1(3) Root(4) Sel(0) N(2) A(0) C(4)'.split()
    predicted = [Root1(3), Root(3), Sel(0), N(0), Filter(
        0), Filter(2), Filter(2), Root(3), Sel(0), N(0), Filter(0)]
    print(predicted)
    print(correct)
    print(adjust_sketch(predicted, correct))
