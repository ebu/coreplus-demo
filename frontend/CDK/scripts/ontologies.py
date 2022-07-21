import sys
from turtle import width
import uuid
import requests
import pandas as pd
from .config import *
from itables import show
from pyvis.network import Network


def __flatten__(data, parent={}):

    resultant = []

    for element in data:
        element.update(**parent)
        resultant.append(element)
        element.update({'Class Label': element.pop('label', None)})
        element.update({'Class IRI': element.pop('cls', None)})
        element.update({'Language': element.pop('lang', '')})
        element.update({'hasSubclasses': not element.pop('leaf', False)})

        if element.get('hasSubclasses', None):
            children = element.pop('children')
            _parent = {
                'Superclass Labels': element.get('Class Label'),
                'Superclass IRIs': element.get('Class IRI'),
                'Superclass Language': element.get('Language')
            }
            resultant += __flatten__(data=children, parent=_parent)

    return resultant


def __get_access_token__(username, password):

    url = f'{URL}/auth/realms/{TENANT}/protocol/openid-connect/token'

    body = {
        'grant_type': 'password',
        'client_id': 'enapso-sdk',
        'username': username,
        'password': password
    }

    try:
        response = requests.post(url=url, data=body)
        response.raise_for_status()
    except requests.exceptions.RequestException as exception:
        sys.stdout.write(str(exception))
        return None

    access_token = response.json()
    access_token = access_token.get('access_token')

    return access_token


def __get_classes__(access_token):

    url = f'{URL}{ENAPSO_NAMESPACE}/v1/get-all-classes'

    headers = {
        'Content-Type': 'application/json',
        'x-enapso-auth': access_token
    }

    try:
        body = {
            'graph':  GRAPH,
        }

        response = requests.post(url=url, headers=headers, json=body)
        response.raise_for_status()
    except requests.exceptions.RequestException as exception:
        sys.stdout.write(exception)
        return None

    classes = response.json()
    classes = __flatten__(classes.get('records'))

    return classes


def __get_descriptions__(access_token):

    url = f'{URL}{ENAPSO_NAMESPACE}/v1/get-classes-description'

    headers = {
        'Content-Type': 'application/json',
        'x-enapso-auth': access_token
    }

    try:
        body = {
            'graph': GRAPH,
        }
        response = requests.post(url=url, headers=headers, json=body)
        response.raise_for_status()
    except requests.exceptions.RequestException as exception:
        sys.stdout.write(str(exception))
        return None

    descriptions = response.json()
    descriptions = descriptions.get('records')

    descriptions_ = {}
    for item in descriptions:
        if not item.get('descriptionLang', None) and \
                not item.get('description', None):
            continue
        entity = item.get('entity')
        if entity in descriptions_:
            descriptions_.get(entity).update(
                {item.get('descriptionLang'): item.get('description')})
        else:
            descriptions_.update(
                {entity: {item.get('descriptionLang'):
                          item.get('description')}})

    return descriptions_


def __remove_nans__(df):

    for coulmn in list(df.columns):
        df[coulmn] = df[coulmn].fillna('')

    return df


def __extract_labels_from_iris__(iris):

    labels = [iri.split('#')[-1] for iri in iris if iri]

    return labels


def __accquire_properties__(iri, username, password):

    properties = get_properties(iri=iri,
                                username=username,
                                password=password,
                                show_table=False,
                                raw=True)

    properties_ = {}

    for item in properties:
        prop_type = item.get('type', '')
        if prop_type.split('#'):
            prop_type = prop_type.split('#')[-1]

        prop_ = item.get('prop', '')

        range_ = item.get('range', '')

        if prop_type in properties_:
            existing = properties_.get(prop_type)
            existing.append({
                            'property': prop_,
                            'range': range_,
                            'type': prop_type.lower()
                            })
            properties_.update({prop_type: existing})
        else:
            properties_.update({prop_type: [{
                                            'property': prop_,
                                            'range': range_,
                                            'type': prop_type.lower()
                                            }]
                                })

    return properties_


def __accquire_description__(username, password):

    access_token = __get_access_token__(username, password)

    descriptions = __get_descriptions__(access_token=access_token)

    return descriptions


def itable_config(opt, init_notebook_mode):
    """A callable-only function to configure itable for notebook.

    Args:
        opt (module): Object used to configure itables.
        init_notebook_mode (function): Function used to toggle interactive mode for notebook.
    """

    opt.maxBytes = 0
    opt.lengthMenu = [5, 10, 25, 50, -1]
    opt.classes = ['cell-border', 'stripe', 'hover']
    init_notebook_mode(all_interactive=True)


def get_individuals(iri, username, password, show_table=True):
    """A function that acquires individuals for the given IRI.

    Args:
        iri (string): The IRI to query individuals for.
        username (string): Username to access API.
        password (string): Password to access API.
        show_table (bool, optional): Flag for displaying the table. Defaults to True.

    Returns:
        (DataFrame, optional): The DataFrame holding the individuals.
    """

    url = f'{URL}{INDIVIDUAL_NAMESPACE}/v1/read-individual'

    access_token = __get_access_token__(username=username, password=password)

    headers = {
        'Content-Type': 'application/json',
        'x-enapso-auth': access_token
    }

    try:
        body = {'cls': iri}
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


def load_model(username, password):
    """Acquires model for the notebook.

    Args:
        username (string): Username to access API.
        password (string): Password to access API.

    Returns:
        (DataFrame, optional): The DataFrame holding the model.
    """

    def __merge_with_descriptions__(classes):

        descriptions = __get_descriptions__(access_token=access_token)

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

    access_token = __get_access_token__(username=username, password=password)

    if not access_token:
        return None

    classes = __get_classes__(access_token=access_token)

    __merge_with_descriptions__(classes)

    classes_df = pd.DataFrame(classes)
    classes_df = __remove_nans__(classes_df)

    return classes_df


def get_all_classes(source_df, language='en', show_table=True):
    """Extracts a unqiue DataFrame of classes from the given DataFrame.

    Args:
        source_df (DataFrame): Primary DataFrame to query from.
        language (str, optional): Language to query for. Could accept either of
        these: 'en', 'de' and 'fr'. Defaults to 'en'.
        show_table (bool, optional): Flag for displaying the table. Defaults to True.

    Returns:
        DataFrame: The DataFrame holding the all the classes.
    """

    resultant_df = source_df.copy()
    resultant_df = resultant_df[resultant_df['Language'] == language]
    resultant_df.drop_duplicates(subset='Class IRI', inplace=True)
    resultant_df = resultant_df[resultant_df.columns[resultant_df.columns.isin(
        ['Class Label', 'hasSubclasses', 'Class IRI'])]]
    resultant_df.reset_index(drop=True, inplace=True)

    if show_table:
        show(df=resultant_df,
             columnDefs=[ITABLE_COLDEF],
             eval_functions=True,
             tags=ITABLE_TITLE.format(title=f'List of classes'))

    return resultant_df


def get_classes_by_iris(source_df,
                        iris,
                        show_subclasses=True,
                        show_superclasses=True,
                        language='en',
                        show_table=True):
    """Extracts classes based on give IRIs along with the relations.

    Args:
        source_df (DataFrame): Primary DataFrame to query from.
        iris (list): List of IRIs to query.
        show_subclasses (bool, optional): Flag to extract subclasses. Defaults to True.
        show_superclasses (bool, optional): Flag to extract superclasses. Defaults to True.
        language (str, optional): Language to query for. Could accept either of these: 'en',
        'de' and 'fr'. Defaults to 'en'.
        show_table (bool, optional): Flag to display the table. Defaults to True.

    Returns:
        DataFrame: The DataFrame holding the the queried IRIs.
    """
    extracted_df = source_df.copy()
    extracted_df = extracted_df[(extracted_df['Language'] == language) &
                                (extracted_df['Superclass Language'].isin(
                                    [language, '']))]
    resultant_df = pd.DataFrame()

    for iri in iris:

        class_df = extracted_df.copy()[extracted_df['Class IRI'] == iri]
        resultant_df = pd.concat([resultant_df, class_df])

        if show_subclasses:
            subclasses_df = extracted_df.copy(
            )[extracted_df['Superclass IRIs'] == iri]
            resultant_df = pd.concat([resultant_df, subclasses_df])
        if show_superclasses:
            for _, row in resultant_df['Superclass IRIs'].iteritems():
                superclass_df = extracted_df.copy(
                )[extracted_df['Class IRI'] == row]
                resultant_df = pd.concat([resultant_df, superclass_df])

    resultant_df.sort_values(by=['Class Label'], inplace=True)
    resultant_df.drop_duplicates(
        subset=['Class IRI', 'Superclass IRIs'], inplace=True)
    resultant_df.drop(['Description(French)',
                       'Description(German)',
                       'Description(English)',
                       'Language',
                       'Superclass Language'],
                      axis=1,
                      inplace=True)

    resultant_df.reset_index(drop=True, inplace=True)

    labels = __extract_labels_from_iris__(iris=iris)

    if show_table:
        title = ', '.join(labels)
        if len(labels) > 1:
            title = 'Hierarchy of classes ' + title
        else:
            title = 'Hierarchy of class ' + title

        show(df=resultant_df,
             columnDefs=[ITABLE_COLDEF],
             eval_functions=True,
             tags=ITABLE_TITLE.format(title=title))

    return resultant_df


def get_properties(iri, username, password, show_table=True, raw=False):
    """Acquires propeties for the given IRI.

    Args:
        iri (string): The IRI to acquire properties for.
        username (string): Username to access API.
        password (string): Password to access API.
        show_table (bool, optional): Flag for displaying the table. Defaults to True.
        raw (bool, optional): Flag to get raw data or its DataFrame. Defaults to False.

    Returns:
        DataFrame: The DataFrame holding the properties.
    """
    access_token = __get_access_token__(username, password)

    url = f'{URL}{ENAPSO_NAMESPACE}/v1/get-class-own-properties'

    headers = {
        'Content-Type': 'application/json',
        'x-enapso-auth': access_token
    }

    try:
        body = {'cls': iri}
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

    included_alterantives = {col: alterantives.get(
        col) for col in included_columns}
    properties = properties[properties.columns[properties.columns.isin(
        included_columns)]]
    properties.rename(columns=included_alterantives, inplace=True)
    properties.reset_index(drop=True, inplace=True)
    label = iri.split('#')[-1]

    if show_table:
        show(df=properties,
             columnDefs=[ITABLE_COLDEF],
             eval_functions=True,
             tags=ITABLE_TITLE.format(title=f'Properties of class {label}'))

    return properties


def get_description(source_df, iri, language='en', show_table=True):
    """Extarcts descriptions for the given IRI.

    Args:
        source_df (DataFrame): Primary DataFrame to query from.
        iri (string): IRI to query description for.
        language (str, optional): Language to query for. Defaults to 'en'.
        show_table (bool, optional): Flag to display the table. Defaults to True.

    Returns:
        DataFrame: The DataFrame holding the the description of class.
    """
    resultant_df = source_df.copy()
    resultant_df = resultant_df[(resultant_df['Language'] == language) & (
        resultant_df['Class IRI'] == iri)]

    language = LANGUAGE_ACRONYMS.get(language, 'Undefined')

    resultant_df.drop_duplicates(subset='Class IRI', inplace=True)
    resultant_df = resultant_df[resultant_df.columns[resultant_df.columns.isin(
        ['Class Label', f'Description({language})',  'Class IRI'])]]
    resultant_df.rename(
        columns={f'Description({language})': 'Description'}, inplace=True)
    resultant_df.reset_index(drop=True, inplace=True)

    label = __extract_labels_from_iris__(iris=[iri])[0]

    if show_table:
        show(df=resultant_df,
             columnDefs=[ITABLE_COLDEF],
             eval_functions=True,
             tags=ITABLE_TITLE.format(title=f'Description of class {label}'))

    return resultant_df


# def visualize(username,
#               password,
#               source_df,
#               iris,
#               title='Network Graph',
#               show_properties=False,
#               show_legend=True,
#               show_subclasses=True,
#               show_superclasses=True,
#               language='en',
#               verbose=True):
#     """Generates a network object table for the given list of IRIs.

#     Args:
#         username (string): Username to access API.
#         password (string): Password to access API.
#         source_df (DataFrame): Primary DataFrame to query from.
#         iris (list): List of IRIs to query.
#         title (str, optional): Title of the graph. Defaults to 'Network Graph'.
#         show_properties (bool, optional): Flag to add properties to the network object. Defaults to False.
#         show_legend (bool, optional): Flag to display legend. Defaults to True.
#         show_subclasses (bool, optional): Flag to extract subclasses for the queried IRIs. Defaults to True.
#         show_superclasses (bool, optional): Flag to extract superclasses for the queried IRIs. Defaults to True.
#         language (str, optional): Language to query for. Defaults to 'en'.
#         verbose (bool, optional): Flag to display extended tooltip. Defaults to True.

#     Returns:
#         Network: The Network object loaded with nodes and edges to display.
#     """
#     # Acquiring required DataFrame
#     source_df = get_classes_by_iris(source_df=source_df,
#                                     iris=iris,
#                                     show_subclasses=show_subclasses,
#                                     show_superclasses=show_superclasses,
#                                     language=language,
#                                     show_table=False)
#     # Acquiring descriptions for all classes
#     descriptions = __accquire_description__(
#         username=username, password=password)

#     # Creating a Network object
#     network = Network(height='800px', width='100%',
#                       directed=True, notebook=True, heading=title)
#     network.repulsion(node_distance=300, spring_length=300)

#     # Forming a dictionary out of involved classes
#     nodes = {}
#     for index, row in source_df.iterrows():
#         iri = row.pop('Class IRI')
#         if iri not in nodes:
#             nodes.update({iri: {
#                 'n_id': iri,
#                 **row
#             }
#             })

#     # Extracting labels from the given list of IRIs
#     labels = __extract_labels_from_iris__(iris=iris)

#     # Qualifying classes and generating nodes
#     datatype_property_nodes = {}
#     object_property_nodes = {}
#     for key, value in nodes.items():
#         # Acquiring description for the given IRI
#         description = descriptions.get(key, {}).get(language, None)
#         # Forming description string to display
#         if description:
#             description_ = ''
#             for index, char in enumerate(description):
#                 # Condition is set to display only 200 characters
#                 if index >= 200:
#                     description_ += '...(see complete in visualization)'
#                     break
#                 # Condition is set to add new line after every 50 characters
#                 elif not (index+1) % 50:
#                     description_ += '\n'
#                 description_ += char
#         else:
#             description_ = 'Not available...'

#         # Variable tooltip to hold string for tooltip
#         tooltip = f'Description:\n{description_}'

#         # Acquiring all properties for the given IRI
#         all_properties = __accquire_properties__(
#             iri=key, username=username, password=password)
#         # Extracting datatype properties
#         dtype_props = all_properties.get('DatatypeProperty', '')
#         # Resolving datatype properties string
#         shown_count = 0
#         if dtype_props:
#             datatype_properties_ = ''
#             for count, (_prop_, _instance_) in enumerate(dtype_props.items()):
#                 datatype_property_nodes.update({_prop_: {
#                                                 'n_id': randint(0, 1000),
#                                                 'pn_id': value.get('n_id'),
#                                                 'edge': _instance_
#                                                 }
#                                                 })

#                 if count < 3:
#                     datatype_properties_ += f'• {_prop_}\n'
#                     shown_count = count+1
#                 elif count == 3:
#                     datatype_properties_ += f'(see complete in visualizations)'

#         else:
#             datatype_properties_ = 'Not available...'
#         total = len(dtype_props)
#         datatype_properties_ = f'\n\nDatatype Properties' \
#                                 f'[{shown_count}/{total}]:' \
#                                 f'\n{datatype_properties_}'

#         # Extracting object properties
#         object_props = all_properties.get('ObjectProperty', '')
#         # Resolving object properties text
#         shown_count = 0
#         if object_props:
#             object_properties_ = ''
#             for count, (_prop_, _instance_) in enumerate(object_props.items()):
#                 object_property_nodes.update({_prop_: {
#                     'n_id': randint(1000, 2000),
#                     'pn_id': value.get('n_id'),
#                     'edge': _instance_
#                 }
#                 })
#                 if count < 3:
#                     object_properties_ += f'• {_prop_}\n'
#                     shown_count = count+1
#                 elif count == 3:
#                     object_properties_ += f'(see complete in visualizations)'

#         else:
#             object_properties_ = 'Not available...'
#         total = len(object_props)
#         object_properties_ = f'\nObject Properties [{shown_count}/{total}]:'\
#                               f'\n{object_properties_}'
#         # Adding properties to tooltip if verbose is set
#         if verbose:
#             tooltip += datatype_properties_
#             tooltip += object_properties_
#         # Color selection based of class characteristics
#         if value.get('hasSubclasses'):
#             color = '#ABEBC6'
#         else:
#             color = '#ACF'
#         # Width selection for quried classes
#         if value.get('Class Label') in labels:
#             borderWidth = 3
#             borderWidthSelected = 3
#         else:
#             borderWidth = 1
#             borderWidthSelected = 2
#         # Adding nodes to the Network object
#         network.add_node(n_id=value.get('n_id'),
#                          label=value.get('Class Label'),
#                          borderWidthSelected=borderWidthSelected,
#                          borderWidth=borderWidth,
#                          title=tooltip,
#                          color=color,
#                          shape='dot',
#                          size=40)

#     # Adding edges to the network
#     for key, value in nodes.items():
#         parent = value.get('Superclass IRIs', None)
#         if parent:
#             _to = value.get('n_id', None)
#             _from = nodes.get(parent, {}).get('n_id', None)
#             if _to and _from:
#                 network.add_edge(source=_to, to=_from,
#                                  arrowStrikethrough=False, color='#AEB6BF')

#     # Adding properties to the Network object if show_properties is set
#     if show_properties:
#         network.set_edge_smooth('cubicBezier')
#         network.repulsion(node_distance=500, spring_length=400)
#         # Addind datatype properties to the Network object
#         for key, value in datatype_property_nodes.items():
#             n_id = value.get('n_id')
#             network.add_node(n_id=n_id,
#                              label=value.get('edge'),
#                              borderWidthSelected=1,
#                              borderWidth=1,
#                              color='#FC3',
#                              shape='box',
#                              size=40,
#                              x=-700,
#                              y=-600)
#             _from = value.get('pn_id')
#             network.add_edge(source=_from, to=n_id, arrowStrikethrough=False,
#                              color='#000', width=1, label=key)
#         # Addind object properties to the Network object
#         for key, value in object_property_nodes.items():
#             n_id = value.get('n_id')
#             network.add_node(n_id=n_id,
#                              label=value.get('edge'),
#                              borderWidthSelected=1,
#                              borderWidth=1,
#                              color='#ACf',
#                              shape='dot',
#                              size=40,
#                              x=-700,
#                              y=-600)
#             _from = value.get('pn_id')
#             network.add_edge(source=_from,
#                              to=n_id,
#                              arrowStrikethrough=False,
#                              color='#000',
#                              width=1,
#                              label=key)
#     # Displaying legend
#     if show_legend & show_properties:
#         network.add_node(n_id=-1,
#                          label=' ',
#                          shape='image',
#                          image=FULL_LEGEND,
#                          size=100,
#                          x=-1000,
#                          y=-500,
#                          fixed=True)
#     else:
#         network.add_node(n_id=-1,
#                          label=' ',
#                          shape='image',
#                          image=SHORT_LEGEND,
#                          size=100,
#                          x=-700,
#                          y=-200,
#                          fixed=True)
#     # Return the network object holding all the nodes and edges
#     return network


def visualize(username,
              password,
              source_df,
              iris,
              title='Network Graph',
              show_properties=False,
              show_legend=True,
              show_subclasses=True,
              show_superclasses=True,
              language='en',
              verbose=True):
    """Generates a Network object for the given list of IRIs.

    Args:
        username (string): Username to access API.
        password (string): Password to access API.
        source_df (DataFrame): Primary DataFrame to query from.
        iris (list): List of IRIs to query.
        title (str, optional): Title of the graph. Defaults to 'Network Graph'.
        show_properties (bool, optional): Flag to add properties to the network object. Defaults to False.
        show_legend (bool, optional): Flag to display legend. Defaults to True.
        show_subclasses (bool, optional): Flag to extract subclasses for the queried IRIs. Defaults to True.
        show_superclasses (bool, optional): Flag to extract superclasses for the queried IRIs. Defaults to True.
        language (str, optional): Language to query for. Could accept either of these: 'en', 'de' and 'fr'.
        Defaults to 'en'.
        verbose (bool, optional): Flag to display extended tooltip. Defaults to True.

    Returns:
        Network: The Network object loaded with nodes and edges to display.
    """
    def format_description(description):

        if description:
            description_ = 'Description:\n'
            for index, char in enumerate(description):
                # Condition is set to display only 200 characters
                if index >= 200:
                    description_ += '...(see complete in visualization)'
                    break
                # Condition is set to add new line after every 50 characters
                elif not (index+1) % 50:
                    description_ += '\n'
                description_ += char
        else:
            description_ = 'Not available...'

        return description_

    def format_properties(properties):

        count_ = 0
        tooltip_ = ''
        properties_ = properties.get('DatatypeProperty', '')

        for count, prop in enumerate(properties_):
            property_ = prop.get('property').split('#')[-1]
            if count < 3:
                tooltip_ += f"• {property_}\n"
                count_ = count+1
            elif count == 3:
                tooltip_ += '...(see complete in visualizations)'
        tooltip_ = f'\n\nDatatype Properties: [{count_}/{len(properties_)}]\n' + \
            tooltip_

        count_ = 0
        tooltip__ = ''
        properties_ = properties.get('ObjectProperty', '')

        for count, prop in enumerate(properties_):
            property_ = prop.get('property').split('#')[-1]
            if count < 3:
                tooltip__ += f"• {property_}\n"
                count_ = count+1
            elif count == 3:
                tooltip__ += '...(see complete in visualizations)'
        tooltip__ = f'\nObject Properties: [{count_}/{len(properties_)}]\n' + \
            tooltip__

        return tooltip_ + tooltip__

    def qualify_class(iri):

        extracted_df = source_df[(source_df['Language'] == language) &
                                 (source_df['Superclass Language'].isin(
                                     [language, '']))]
        extracted_df = extracted_df.copy()[extracted_df['Class IRI'] == iri]
        extracted_df.drop_duplicates(
            subset=['Class IRI', 'Superclass IRIs'], inplace=True)
        if not extracted_df.empty:
            label = extracted_df['Class Label'].values[0]
            color = SUPERCLASS_COLOR if extracted_df['hasSubclasses'].values[0] else SUBCLASS_COLOR
        else:
            label = iri.split('#')[-1]
            color = SUPERCLASS_COLOR

        data = {
            'label': label,
            'color': color,
            'shape': CLASS_SHAPE
        }

        return data

    # Creating a Network object
    network = Network(height='800px', width='100%',
                      directed=True, notebook=True, heading=title)
    network.repulsion(node_distance=300, spring_length=300)

    # Acquiring required DataFrame
    resultant_df = get_classes_by_iris(source_df=source_df,
                                       iris=iris,
                                       show_subclasses=show_subclasses,
                                       show_superclasses=show_superclasses,
                                       language=language,
                                       show_table=False)

    # Acquiring descriptions for all classes
    descriptions = __accquire_description__(
        username=username, password=password)

    # Forming a dictionaries out of involved classes and properties
    nodes = {}
    edges = []
    for _, row in resultant_df.iterrows():
        iri = row.get('Class IRI')
        superclass_iri = row.get('Superclass IRIs')
        description = descriptions.get(iri, {}).get(language, None)

        # Creating edge for classes
        if superclass_iri:
            edge = {
                'parent_node_id': superclass_iri,
                'child_node_id': iri,
                'color': CLASS_EDGE_COLOR
            }
            edges.append(edge)
        # Creating nodes for classes. The key 'reset' indicates that the data for the
        # IRI was populated by a object property, so we need to qualify it.
        if nodes.get(iri, {}).get('reset', True):
            node = {
                'node_id': iri,
                'label': row.get('Class Label'),
                'tooltip': format_description(description),
                'color': SUPERCLASS_COLOR if row.get('hasSubclasses', False) else SUBCLASS_COLOR,
                'shape': CLASS_SHAPE,
                'size': NODE_SIZE,
                'reset': False
            }

            # Larger width for nodes of focus
            if iri in iris:
                node.update({'width': 4})

            all_properties = __accquire_properties__(iri=iri,
                                                     username=username,
                                                     password=password)
            # Adding properties to tooltip
            if verbose:
                node.update({'tooltip': node.get('tooltip') +
                            format_properties(all_properties)})

            nodes.update({iri: node})

            # Adding nodes for properties
            if show_properties:
                properties = all_properties.get('DatatypeProperty', [])

                properties += all_properties.get('ObjectProperty', [])

                for property_ in properties:
                    range_ = property_.get('range')
                    if range_ not in nodes:
                        node = {
                            'node_id': range_,
                            'label': range_.split('#')[-1],
                            'size': NODE_SIZE,
                            'reset': True
                        }

                        # Configuring datatype and object properties differently
                        if property_.get('type') == 'objectproperty':
                            description = descriptions.get(
                                range_, {}).get(language, None)

                            node.update(**qualify_class(iri=range_))
                            node.update(
                                {'tooltip': format_description(description)})

                            if verbose:
                                all_properties = __accquire_properties__(iri=range_,
                                                                         username=username,
                                                                         password=password)
                                node.update({'tooltip': node.get(
                                    'tooltip')+format_properties(all_properties)})
                        else:
                            range_ = node.get('node_id')+str(uuid.uuid4())
                            node.update({'node_id': range_})
                            node.update({'color': DATATYPE_PROPERTY_COLOR})
                            node.update({'shape': DATATYPE_PROPERTY_SHAPE})

                        nodes.update({range_: node})

                    # Addig edge for properties
                    edge = {
                        'parent_node_id': range_,
                        'child_node_id': iri,
                        'label': property_.get('property').split('#')[-1],
                        'color': PROPERTY_EDGE_COLOR
                    }
                    edges.append(edge)

    # Add nodes to the graph
    for _, value in nodes.items():
        network.add_node(n_id=value.get('node_id'),
                         color=value.get('color'),
                         label=value.get('label'),
                         shape=value.get('shape'),
                         size=value.get('size'),
                         title=value.get('tooltip', ''),
                         borderWidth=value.get('width', 1),
                         borderWidthSelected=value.get('width', 1)+1)

    # Add edges to the graph
    for edge in edges:
        to = edge.get('parent_node_id')
        source = edge.get('child_node_id')
        if to in nodes.keys() and source in nodes.keys():
            network.add_edge(to=to,
                             source=source,
                             label=edge.get('label', ' '),
                             color=edge.get('color'),
                             arrowStrikethrough=True)

    # Display the legend
    if show_legend and show_properties:
        network.add_node(n_id=-99999,
                         label=' ',
                         shape='image',
                         image=FULL_LEGEND,
                         size=100,
                         x=-700,
                         y=-200,
                         fixed=True)
    elif show_legend:
        network.add_node(n_id=-99999,
                         label=' ',
                         shape='image',
                         image=SHORT_LEGEND,
                         size=100,
                         x=-700,
                         y=-200,
                         fixed=True)
    return network
