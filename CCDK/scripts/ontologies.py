import sys
import random
import requests
import pandas as pd
from pyvis.network import Network
from itables import show
from .config import *

# Tested 
def _flatten(data, parent={}):
    
    resultant = []
    for element in data:
        element.update(**parent)
        resultant.append(element)
        element.update({'Class Label': element.pop('label')})
        element.update({'Class IRI': element.pop('cls')})
        element.update({'Language': element.pop('lang', '')})
        element.update({'hasNoSubclasses': element.pop('leaf', False)})

        if not element.get('hasNoSubclasses', None):
            children = element.pop('children')
            _parent = {
                    'Superclass Labels' : element.get('Class Label'),
                    'Superclass IRIs' : element.get('Class IRI'),
                    'Superclass Language' : element.get('Language')
                    }
            resultant += _flatten(data=children, parent=_parent)

    return resultant

# Tested 
def _get_access_token(username, password):
    
    url = f'{BASE_URL}/auth/realms/{DEMO_TENANT_ID}/protocol/openid-connect/token'

    body = {
        'grant_type' : 'password',
        'client_id' : 'enapso-sdk',
        'username' : username,
        'password' : password
    }
    
    try:
        response = requests.post(url=url, data=body)
        response.raise_for_status()
    except requests.exceptions.RequestException as exception:
        sys.stdout.write(str(exception))
        sys.stdout.write('\n')
        return None
    
    access_token = response.json()
    access_token = access_token.get('access_token')
    
    return access_token

# Tested 
def _get_classes(access_token):

    url = f'{BASE_URL}{NAMESPACE}/v1/get-all-classes'   
    
    headers = {
        'Content-Type' : 'application/json',
        'x-enapso-auth' : access_token
    }
    
    try:
        body = { 
            'graph':  EBUCORE_GRAPH,
        }

        response = requests.post(url=url, headers=headers, json=body)
        response.raise_for_status()
    except requests.exceptions.RequestException as exception:
        sys.stdout.write(exception)
        return None
    
    classes = response.json()
    classes = _flatten(classes.get('records'))    
    
    return classes

# Tested        
def _get_descriptions(access_token):
    
    url = f'{BASE_URL}{NAMESPACE}/v1/get-classes-description'
    headers = {
        'Content-Type' : 'application/json',
        'x-enapso-auth' : access_token
    }
    
    try:
        body = { 
            'graph': EBUCORE_GRAPH,
        }
        response = requests.post(url=url, headers=headers, json=body)
        response.raise_for_status()
    except requests.exceptions.RequestException as exception:
        sys.stdout.write(str(exception))
        sys.stdout.write('\n')
        return False
    
    descriptions = response.json()
    descriptions = descriptions.get('records')
    
    processed_descriptions = {}
    for item in descriptions:
        if not item.get('descriptionLang', None) and not item.get('description', None):
            continue
        entity = item.get('entity')
        if entity in processed_descriptions:
            processed_descriptions.get(entity).update({item.get('descriptionLang'): item.get('description')})
        else:
            processed_descriptions.update({entity: {item.get('descriptionLang'): item.get('description')}})
        
    return processed_descriptions

# Tested   
def get_individual(iri, username, password, show_table=True):
    
    url = f'{BASE_URL}{INDIVIDUAL_NAMESPACE}/v1/read-individual'
    
    access_token = _get_access_token(username=username, password=password)
    
    headers = {
        'Content-Type' : 'application/json',
        'x-enapso-auth' : access_token
    }
    
    try:
        body = {"cls": iri}
        response = requests.post(url=url, headers=headers, json=body)
        response.raise_for_status()
    except requests.exceptions.RequestException as exception:
        return False, str(exception)
    
    individuals = response.json()
    individuals = individuals.get('records')
    individuals_df = pd.DataFrame(data=individuals)
    
    label = iri.split('#')[-1]
    if show_table:
        show(df=individuals_df, 
        columnDefs=[ITABLE_COLDEF], 
        eval_functions=True, 
        tags=ITABLE_TITLE.format(title=f'Individuals of class {label}'))        

    return individuals_df

# Tested
def get_model(username, password):
    
    def _merge(classes, descriptions):
        for element in classes:
            iri = element.get('Class IRI')
            description = descriptions.get(iri, None)
            if description:
                for key, value in description.items():
                    
                    if key == 'en':
                        key = 'English'
                    elif key == 'de':
                        key = 'German'
                    elif key == 'fr':
                        key = 'French'

                    element.update({f'Description({key})': value})

    access_token = _get_access_token(username=username, password=password)

    if not access_token:
        return None
    
    classes = _get_classes(access_token=access_token)

    descriptions = _get_descriptions(access_token=access_token)
    
    _merge(classes, descriptions)

    classes_df = pd.DataFrame(classes)
    # classes_df.columns = ['Class Label', 'Class IRI', 'hasNoSubclasses', 'Language', 'Superclass Labels', 'Superclass IRIs', 'Superclass Language']
    classes_df['hasNoSubclasses'] = classes_df['hasNoSubclasses'].fillna(False)
    classes_df['Language'] = classes_df['Language'].fillna('')
    classes_df['Superclass Labels'] = classes_df['Superclass Labels'].fillna('')
    classes_df['Superclass IRIs'] = classes_df['Superclass IRIs'].fillna('')
    classes_df['Superclass Language'] = classes_df['Superclass Language'].fillna('')
    
    return classes_df

# Tested
def get_all_classes(source_df, language='en', show_table=True):
    
    resultant_df = source_df.copy()
    resultant_df = resultant_df[resultant_df['Language'] == language]
    resultant_df.drop_duplicates(subset='Class IRI', inplace=True)
    resultant_df = resultant_df[['Class Label', 'hasNoSubclasses', 'Class IRI']]
    resultant_df.reset_index(drop=True, inplace=True)
    
    if language == 'en':
        language = 'English'
    elif language == 'fr':
        language = 'French'
    elif language == 'de':
        language = 'German'
    else:
        language = 'Undefined'
    
    if show_table:
        show(df=resultant_df, 
            columnDefs=[ITABLE_COLDEF], 
            eval_functions=True, 
            tags=ITABLE_TITLE.format(title=f'List of classes'))
        
    return resultant_df

# Tested 
def get_classes_by_labels(source_df, labels, show_subclasses=True, show_superclasses=True, language='en', show_table=True):
    
    extracted_df = source_df.copy()
    #  & (extracted_df['Superclass Language'].isin([language, '']))
    extracted_df = extracted_df[(extracted_df['Language']==language) & (extracted_df['Superclass Language'].isin([language, '']))]
    # return extracted_df
    resultant_df = pd.DataFrame()
    
    for label in labels:
        class_df = extracted_df.copy()[extracted_df['Class Label'] == label]
        resultant_df = pd.concat([resultant_df, class_df])
        
        if show_subclasses:
            subclasses_df = extracted_df.copy()[extracted_df['Superclass Labels'] == label]  
            resultant_df = pd.concat([resultant_df, subclasses_df])
        if show_superclasses:
            for _, row in resultant_df['Superclass IRIs'].iteritems():
                superclass_df = extracted_df.copy()[extracted_df['Class IRI'] == row] 
                resultant_df = pd.concat([resultant_df, superclass_df])
    
    
    resultant_df.sort_values(by=['Class Label'], inplace=True)
    resultant_df.drop_duplicates(subset=['Class IRI', 'Superclass IRIs'], inplace=True)
    resultant_df.drop(['Description(French)', 'Description(German)', 'Description(English)', 'Language', 'Superclass Language'], axis=1, inplace=True)

    resultant_df.reset_index(drop=True, inplace=True)
    
    if language == 'en':
        language = 'English'
    elif language == 'fr':
        language = 'French'
    elif language == 'de':
        language = 'German'
    else:
        language = 'Undefined'
    
    if show_table: 
        title = ', '.join(labels)   
        show(df=resultant_df, 
            columnDefs=[ITABLE_COLDEF], 
            eval_functions=True, 
            tags=ITABLE_TITLE.format(title=f'Hierarchy of class {title}'))

    return resultant_df

# Tested 
def get_leafs(source_df, language='en', show_table=True):

    resultant_df = source_df.copy()
    
    resultant_df = resultant_df[(resultant_df['hasNoSubclasses'] == True) & (resultant_df['Language'] == language)]
    resultant_df.drop_duplicates(subset=['Class IRI', 'Superclass IRIs'], inplace=True)
    resultant_df = resultant_df[['Class Label', 'Class IRI', 'Superclass Labels', 'Superclass IRIs']]
    resultant_df.reset_index(drop=True, inplace=True)
    
    if language == 'en':
        language = 'English'
    elif language == 'fr':
        language = 'French'
    elif language == 'de':
        language = 'German'
    else:
        language = 'Undefined'
    
    if show_table:    
        show(df=resultant_df, 
            columnDefs=[ITABLE_COLDEF], 
            eval_functions=True, 
            tags=ITABLE_TITLE.format(title=f'Leaf classes in {language}'))

    return resultant_df

# Tested 
def get_non_leafs(source_df, language='en', show_table=True):
    
    resultant_df = source_df.copy()
    resultant_df = resultant_df[(resultant_df['hasNoSubclasses'] == False) & (resultant_df['Language'] == language)]
    resultant_df.drop_duplicates(subset=['Class IRI', 'Superclass IRIs'], inplace=True)
    resultant_df = resultant_df[['Class Label', 'Class IRI', 'Superclass Labels', 'Superclass IRIs']]
    resultant_df.reset_index(drop=True, inplace=True)
    
    if language == 'en':
        language = 'English'
    elif language == 'fr':
        language = 'French'
    elif language == 'de':
        language = 'German'
    else:
        language = 'Undefined'
    
    if show_table:
        show(df=resultant_df, 
            columnDefs=[ITABLE_COLDEF], 
            eval_functions=True, 
            tags=ITABLE_TITLE.format(title=f'Non-leaf classes in {language}'))

    return resultant_df

# Tested 
def get_subclasses(source_df, language='en', show_table=True):
    
    resultant_df = source_df.copy()
    resultant_df = resultant_df[(resultant_df['Superclass Labels'] != '') & (resultant_df['Language'] == language)]
    resultant_df.drop(['Language'], axis=1, inplace=True)
    resultant_df.drop_duplicates(subset=['Class IRI', 'Superclass IRIs'], inplace=True)
    resultant_df = resultant_df[['Class Label', 'Class IRI', 'hasNoSubclasses', 'Superclass Labels', 'Superclass IRIs']]
    resultant_df.reset_index(drop=True, inplace=True)

    if language == 'en':
        language = 'English'
    elif language == 'fr':
        language = 'French'
    elif language == 'de':
        language = 'German'
    else:
        language = 'Undefined'
    
    if show_table:    
        show(df=resultant_df, 
            columnDefs=[ITABLE_COLDEF], 
            eval_functions=True, 
            tags=ITABLE_TITLE.format(title=f'Subclasses classes in {language}'))

    return resultant_df

# Tested but needs consideration regardung naming convention
def get_non_subclasses(source_df, language='en', show_table=True):
    
    resultant_df = source_df.copy()
    resultant_df = resultant_df[(source_df['Superclass Labels'] == '') & (source_df['Language'] == language)]
    resultant_df.drop(['Language'], axis=1, inplace=True)
    resultant_df.drop_duplicates(subset='Class IRI', inplace=True)
    resultant_df = resultant_df[['Class Label', 'Class IRI', 'hasNoSubclasses']]
    resultant_df.reset_index(drop=True, inplace=True)

    if language == 'en':
        language = 'English'
    elif language == 'fr':
        language = 'French'
    elif language == 'de':
        language = 'German'
    else:
        language = 'Undefined'
    
    if show_table:
        show(df=resultant_df, 
            columnDefs=[ITABLE_COLDEF], 
            eval_functions=True, 
            tags=ITABLE_TITLE.format(title=f'Non-children classes in {language}'))

    return resultant_df[['Class Label', 'Class IRI', 'hasNoSubclasses']]

# Tested
def get_description(source_df, label, language='en', show_table=True):

    resultant_df = source_df.copy()
    resultant_df = resultant_df[(resultant_df['Language'] == language) & (resultant_df['Class Label'] == label)]
    
    if language == 'en':
        language = 'English'
    elif language == 'fr':
        language = 'French'
    elif language == 'de':
        language = 'German'
    else:
        language = 'English'
    
    resultant_df.drop_duplicates(subset='Class IRI', inplace=True)
    resultant_df = resultant_df[['Class Label', f'Description({language})',  'Class IRI']]
    resultant_df.rename(columns = {f'Description({language})':'Description'}, inplace = True)
    resultant_df.reset_index(drop=True, inplace=True)
    
    if show_table:
        show(df=resultant_df, 
            columnDefs=[ITABLE_COLDEF], 
            eval_functions=True, 
            tags=ITABLE_TITLE.format(title=f'Description of class {label}'))
        
    return resultant_df

# Tested 
def get_properties(iri, username, password, show_table=True, raw=False):
    
    
    access_token = _get_access_token(username, password)
    url = f'{BASE_URL}{NAMESPACE}/v1/get-class-own-properties'
    headers = {
        'Content-Type' : 'application/json',
        'x-enapso-auth' : access_token
    }
    
    try:
        body = { 
            'cls': iri 
        }
        response = requests.post(url=url, headers=headers, json=body)
        response.raise_for_status()
    
    except requests.exceptions.RequestException as exception:
        return False
    
    properties = response.json()
    properties = properties.get('records')

    
    
    if raw:
        return properties
    
    for property in properties:
        for key, value in property.items():
            if key in ['prop', 'type', 'range', 'some']:
                prefix = value.split('#')[0]+'#'
                if prefix in PREFIXES:
                    prefix = PREFIXES.get(prefix)+f":{value.split('#')[1]}"
                    property.update({key: prefix})

    properties = pd.DataFrame(data=properties)

    alterantives = {
                'prop': 'Property',
                'type': 'Type',
                'range': 'Range',
                'max': 'Max Cardinality',
                'some': 'Some Values From'
    }
    
    columns = list(properties.columns)
    included_columns = ['prop', 'type', 'range']
    
    if 'max' in columns:
        included_columns.append('max')
        properties['max'] = properties['max'].fillna('')        
    if 'type' in columns:
        included_columns.append('type')
    if 'some' in columns:
        included_columns.append('some')
        properties['some'] = properties['some'].fillna('')
    
    included_alterantives = {col: alterantives.get(col) for col in included_columns}
    
    # properties = properties[[*included_columns]]
    properties =  properties[properties.columns[properties.columns.isin(included_columns)]]
    properties.rename(columns=included_alterantives, inplace=True)
    
    
    properties.reset_index(drop=True, inplace=True)
    label = iri.split('#')[-1]
    # print('YESSSSSSSSSS', type(properties))
    if show_table:
        show(df=properties, 
            columnDefs=[ITABLE_COLDEF], 
            eval_functions=True, 
            tags=ITABLE_TITLE.format(title=f'Properties of class {label}'))  

    return properties


def _accquire_attrs(iri, username, password):
    response = get_properties(iri=iri, 
                            username=username, 
                            password=password, 
                            show_table=False, 
                            raw=True)

    attrs = {}
    
    for item in response:
        type_ = item.get('type').split('#')[-1]
        prop_ = item.get('prop').split('#')[-1]
        range = item.get('range').split('#')[-1]
        if type_ in attrs:
            existing = attrs.get(type_)
            existing.update({prop_: range})
            attrs.update({type_: existing})
        else:
            attrs.update({type_: {prop_: range}})

    return attrs

def _accquire_description(username, password):

    access_token = _get_access_token(username, password)
    
    descriptions = _get_descriptions(access_token=access_token)

    return descriptions

def visualize(source_df, labels, title='Network Graph', show_properties=False, show_legend=True, show_subclasses=True, show_superclasses=True, language='en', verbose=True):
    
    source_df = get_classes_by_labels(source_df=source_df, 
                                              labels=labels, 
                                              show_subclasses=show_subclasses, 
                                              show_superclasses=show_superclasses, 
                                              language=language,
                                              show_table=False)
    
    descriptions = _accquire_description('demo-user', 'demo')
    nodes = {}
    parents = {}
    for index, row in source_df.iterrows():
        iri = row.pop('Class IRI')
        if not iri in nodes:
            nodes.update({iri: {
                                'n_id': random.randint(0,100),
                                **row
                                }
                        })
    net = Network("800px", "100%", notebook=True, directed=True, heading=title)
    
        
    data_props_nodes = {}
    object_props_nodes = {}
    for key, value in nodes.items():
        if language == 'en':
            _lang = 'English'
        elif language == 'fr':
            _lang = 'French'
        elif language == 'de':
            _lang = 'German'
        else:
            _lang = 'English'
            
        description = descriptions.get(key, {}).get(language, None)
        
        if description:
            description_html = ''
            for index, char in enumerate(description):
                if index >= 200:
                    description_html += '...<span style="font-style: oblique;text-decoration: underline;">(see complete in visualization)</span>'
                    break
                elif not (index+1)%50:
                    description_html += '<br>'
                description_html += char
        else:
            description_html = 'Not available...'
        description = f'<span style="letter-spacing:0.9px;"><span style="font-weight:bold;">Description</span><br>{description_html}</span>'
        
        
        props = _accquire_attrs(iri=key, username='demo-user', password='demo')
        # print(props)
        data_props = props.get('DatatypeProperty', '')
        
        show_count = 0
        count_flag = True
        if data_props: 
            data_props_html = ''
            for _prop_, _instance_ in data_props.items():
                data_props_nodes.update({_prop_: {
                                                'n_id': random.randint(0, 10000),
                                                'pn_id': value.get('n_id'),
                                                'edge': _instance_
                                                }
                                        })
                
                if count_flag & (show_count < 3):
                    data_props_html += f'<span>&#8226; {_prop_}</span><br>'
                    show_count += 1
                elif count_flag & (show_count == 3):
                    data_props_html += f'...<span style="font-style: oblique;text-decoration: underline;">(see complete in visualizations)</span>'
                    count_flag = False
                
        else:
            data_props_html = 'Not available...'
        
        if show_count == -1:
            show_count = 0

        data_props_html = f'<br><br><span style="letter-spacing:0.9px;"><span style="font-weight:bold;">Datatype Properties({show_count}/{len(data_props)})</span><br>{data_props_html}</span>'
        if verbose:
            description += data_props_html  

        object_props = props.get('ObjectProperty', '')
        show_count = 0
        count_flag = True
        if object_props: 
            object_props_html = ''
            
            for _prop_, _instance_ in object_props.items():
                object_props_nodes.update({_prop_: {
                                                'n_id': random.randint(0,400),
                                                'pn_id': value.get('n_id'),
                                                'edge': _instance_
                                                }
                                        })
                if count_flag & (show_count < 3):
                    object_props_html += f'<span>&#8226; {_prop_}</span><br>'
                    show_count += 1
                elif count_flag & (show_count == 3):
                    object_props_html += f'...<span style="font-style: oblique;text-decoration: underline;">(see complete in visualizations)</span>'
                    count_flag = False
                
                
        else:
            object_props_html = 'Not available...'
        

        if show_count == -1:
            show_count = 0
            
        object_props_html = f'<br><br><span style="letter-spacing:0.9px;"><span style="font-weight:bold;">Object Properties({show_count}/{len(object_props)})</span><br>{object_props_html}</span>'
        
        if verbose:
            description += object_props_html     
        
        if value.get('hasNoSubclasses'):
            color = '#ABEBC6'
        else:
            color = '#acf'
            
        class_label = value.get('Class Label')
        
        if class_label in labels:
            borderWidth = 3
            borderWidthSelected = 3
        else: 
            borderWidth = 1
            borderWidthSelected = 2
        
        net.add_node(n_id=value.get('n_id'), 
                     label=value.get('Class Label'), 
                     borderWidthSelected=borderWidthSelected, 
                     borderWidth=borderWidth, 
                     title=description, 
                     color=color, 
                     shape='dot', 
                     size=40)
    
    for key, value in nodes.items():
        parent = value.get('Superclass IRIs', None)
        if parent:
            _to = value.get('n_id', None)
            _from = nodes.get(parent, {}).get('n_id', None)
            if _to and _from:
                net.add_edge(_to, _from, arrowStrikethrough=False, color='black')
    
    net.repulsion(node_distance=300, spring_length=300)
    if show_properties:
        net.set_edge_smooth('cubicBezier')
        net.repulsion(node_distance=500, spring_length=400)
        for key, value in data_props_nodes.items():
            n_id = value.get('n_id')
            net.add_node(n_id=n_id, 
                         label=value.get('edge'), 
                         borderWidthSelected=1, 
                         borderWidth=1, 
                         color='#fc3', 
                         shape='box', 
                         size=40,
                         x=-700, 
                         y=-600)
            _from = value.get('pn_id')
            net.add_edge(_from, n_id , arrowStrikethrough=False,  color="#AEB6BF", width=1, label=key)
        
        for key, value in object_props_nodes.items():
            n_id = value.get('n_id')
            net.add_node(n_id=n_id, 
                         label=value.get('edge'), 
                         borderWidthSelected=1, 
                         borderWidth=1, 
                         color='#acf', 
                         shape='dot', 
                         size=40,
                         x=-700, 
                         y=-600)
            _from = value.get('pn_id')
            net.add_edge(_from, n_id , arrowStrikethrough=False,  color="#AEB6BF", width=1, label=key)
        
        net.toggle_stabilization(True)
        if show_legend:
            net.add_node(n_id=-1, label=' ', shape='image', image ="https://res.cloudinary.com/alieymsxxn/image/upload/v1653957217/FULL_LEGEND_rxevl5.png", size=100, x=-1000, y=-500, fixed=True)
    else:
        if show_legend:
            net.add_node(n_id=-1, label=' ', shape='image', image ="https://res.cloudinary.com/alieymsxxn/image/upload/v1653957539/SHORT_LEGEND_ghqnak.png", size=100, x=-700, y=-200, fixed=True)
        
        
    return net

def itable_config(opt, init_notebook_mode):
    opt.lengthMenu = [5, 10, 25, 50, -1] 
    opt.classes = ['cell-border', 'stripe', 'hover']
    opt.maxBytes = 0
    init_notebook_mode(all_interactive=True)
