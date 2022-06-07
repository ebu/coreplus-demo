# from os import access
# import pickle

# # with open('pkl.pkl', 'rb') as file:
# #     data = pickle.load(file)

# # print('got data')

# def flatten(data, parent=''):
#     res = []
#     for element in data:

#         element.update({'parent': parent})
#         res.append(element)
#         if not element.get('leaf', None):
#             children = element.pop('children')
#             if parent: 
#                 _parent = f'{parent}_{element.get("label")}'
#             else: 
#                 _parent = element.get("label")
#             res += flatten(data=children, parent=_parent)

#     return res

from ontologies import get_model, _accquire_attrs, get_properties
if __name__ == '__main__':
    properties = get_properties(iri='http://www.ebu.ch/metadata/ontologies/ebucore/ebucore#EditorialObject', 
                           username='demo-user', 
                           password='demo',
                           show_table=True)
    print('got data')