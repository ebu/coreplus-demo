import sys
import uuid
import requests
import pandas as pd
from .config import *
from itables import show
from pyvis.network import Network


def __validate_args__(arg, flat=False):

    if not flat:
        if not arg or '' in arg:
            raise ValueError('List of IRIs cannot be empty or contain ' +
                             'an empty string.')
    else:
        if '' == arg:
            raise ValueError('IRI cannot be an empty string.')

    return True


def __flatten__(data, parent={}):

    resultant = []

    for element in data:
        element.update(**parent)
        resultant.append(element)
        element.update({'Label': element.pop('label', None)})
        element.update({'IRI': element.pop('cls', None)})
        element.update({'Language': element.pop('lang', '')})
        element.update({'IsLeafClass': element.pop('leaf', False)})

        if not element.get('IsLeafClass', None):
            children = element.pop('children')
            _parent = {
                'Superclass label': element.get('Label'),
                'Superclass IRI': element.get('IRI'),
                'Superclass language': element.get('Language')
            }
            resultant += __flatten__(data=children, parent=_parent)

    return resultant


def __get_access_token__(tenant, username, password):

    url = f'{BASE_URL}/auth/realms/{tenant}/protocol/openid-connect/token'

    body = {
        'grant_type': 'password',
        'client_id': 'enapso-sdk',
        'username': username,
        'password': password
    }

    try:
        response = requests.post(url=url, data=body, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.RequestException as exception:
        sys.stdout.write(str(exception))
        return None

    access_token = response.json()
    access_token = access_token.get('access_token')

    return access_token


def __get_all_classes__(access_token):

    url = f'{BASE_URL}{ENAPSO_NAMESPACE}/v1/get-all-classes'

    headers = {
        'Content-Type': 'application/json',
        'x-enapso-auth': access_token
    }

    try:
        body = {
            'graph': SOURCE_GRAPH,
        }

        response = requests.post(
            url=url, headers=headers, json=body, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.RequestException as exception:
        sys.stdout.write(exception)
        return None

    classes = response.json()
    classes = __flatten__(classes.get('records'))

    return classes

def __get_descriptions__(access_token):

    url = f'{BASE_URL}{TEMPLATE_NAMESPACE}/v1/execute-template'

    headers = {
        'Content-Type': 'application/json',
        'x-enapso-auth': access_token
    }

    try:
        body = {
            "template": "http://www.ebu.ch/metadata/ontologies/ebucoreplus#SPARQLTemplate_e5e398b0-f9de-417a-b5c1-39f793f30f9d",
            "variables": {
                    "language": "en"
                        }
                }
        response = requests.post(
            url=url, headers=headers, json=body, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.RequestException as exception:
        sys.stdout.write(str(exception))
        return None

    descriptions = response.json()
    descriptions = descriptions.get('records')

    descriptions_ = {}
   for item in descriptions:
        if not item.get('description', None):
            continue
        entity = item.get('entity')
        if entity in descriptions_:
            descriptions_.get(entity).update(
                {'description': item.get('description'),
                 'definition': item.get('definition'),
                 'example': item.get('example')})
        else:
            descriptions_.update(
                {entity: {'description': item.get('description'),
                          'definition': item.get('definition'),
                          'example': item.get('example')}})

    return descriptions_


def __remove_nans__(df):

    for column in list(df.columns):
        df[column] = df[column].fillna('')

    return df


def __get_name_from_iri__(iri):

    name = iri.split('#')[-1]
    if len(name) == len(iri):
        name = iri.split('/')[-1]

    return name


def __get_names_from_iris__(iris):

    names = [__get_name_from_iri__(iri) for iri in iris if iri]

    return names


def __acquire_properties__(tenant, username, password, iri):

    properties = get_properties(tenant=tenant,
                                username=username,
                                password=password,
                                iri=iri,
                                show_table=False,
                                raw=True)

    properties_ = {}

    for item in properties:
        prop_type = __get_name_from_iri__(item.get('type', ''))

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


def __acquire_description__(tenant, username, password):

    access_token = __get_access_token__(
        tenant=tenant, username=username, password=password)

    descriptions = __get_descriptions__(access_token=access_token)

    return descriptions


def itable_config(opt, init_notebook_mode):

    """A callable-only function to configure itable for notebook.

    Args:
        opt (module): Object used to configure itables.
        init_notebook_mode (function): Function used to toggle interactive mode
        for notebook.
    """

    opt.maxBytes = 0
    opt.lengthMenu = [5, 10, 25, 50, -1]
    opt.classes = ['cell-border', 'stripe', 'hover']
    init_notebook_mode(all_interactive=True)


def get_individuals(tenant, username, password, iri, show_table=True):

    """It acquires individuals for the given IRI.

    Args:
        tenant (string): Tenant id to access API.
        username (string): Username to access API.
        password (string): Password to access API.
        iri (string): The IRI to query individuals for.
        show_table (bool, optional): Flag for displaying the table.
        Defaults to True.

    Returns:
        (DataFrame, optional): The DataFrame holding the individuals.
    """

    __validate_args__(arg=iri, flat=True)

    url = f'{BASE_URL}{INDIVIDUAL_NAMESPACE}/v1/read-individual'

    access_token = __get_access_token__(
        tenant=tenant, username=username, password=password)

    headers = {
        'Content-Type': 'application/json',
        'x-enapso-auth': access_token
    }

    try:
        body = {'cls': iri}
        response = requests.post(
            url=url, headers=headers, json=body, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.RequestException as exception:
        return False, str(exception)

    individuals = response.json()
    individuals = individuals.get('records')
    individuals_df = pd.DataFrame(data=individuals)

    name = __get_name_from_iri__(iri)

    column_display_names = {
        'iri': 'IRI',
        'alternativeTitle': 'ec:alternativeTitle',
        'contentDescription': 'ec:contentDescription'
    }
    individuals_df.rename(columns=column_display_names, inplace=True)

    if show_table:
        title=f'Individuals of class {name}'
        show(df=individuals_df,
             columnDefs=[ITABLE_COLDEF],
             eval_functions=True,
             tags=ITABLE_TITLE.format(title=title))

    return individuals_df


def load_model(tenant, username, password):

    """It acquires the model for the notebook.

    Args:
        tenant (string): Tenant id to access API.
        username (string): Username to access API.
        password (string): Password to access API.

    Returns:
        (DataFrame, optional): The DataFrame holding the model.
    """

    def __merge_with_descriptions__(classes):

        descriptions = __get_descriptions__(access_token=access_token)

        for element in classes:
            iri = element.get('IRI')
            description = descriptions.get(iri, None)
            if description:
                for key, value in description.items():
                    if key in LANGUAGES:
                        language_term = LANGUAGE_TERMS.get(key, 'Undefined')
                        element.update({f'Description ({language_term})': value})

    access_token = __get_access_token__(
        tenant=tenant, username=username, password=password)

    if not access_token:
        return None

    classes = __get_all_classes__(access_token=access_token)

    __merge_with_descriptions__(classes)

    classes_df = pd.DataFrame(classes)
    classes_df = __remove_nans__(classes_df)

    return classes_df


def get_all_classes(source_df, language='en', show_table=True):

    """It extracts a unique DataFrame of classes from the given DataFrame.

    Args:
        source_df (DataFrame): Primary DataFrame to query from.
        language (str, optional): Language to query for. Could accept either
        of these: 'en', 'de', and 'fr'.
        Defaults to 'en'.
        show_table (bool, optional): Flag for displaying the table.
        Defaults to True.

    Returns:
        DataFrame: The DataFrame holding all the classes.
    """

    resultant_df = source_df.copy()
    resultant_df = resultant_df[resultant_df['Language'] == language]
    resultant_df.drop_duplicates(subset='IRI', inplace=True)
    resultant_df = resultant_df[resultant_df.columns[resultant_df.columns.isin(
        ['Label', 'IsLeafClass', 'IRI'])]]
    resultant_df.reset_index(drop=True, inplace=True)

    if show_table:
        title='List of classes'
        show(df=resultant_df,
             columnDefs=[ITABLE_COLDEF],
             eval_functions=True,
             tags=ITABLE_TITLE.format(title=title))

    return resultant_df


def get_hierarchy(source_df,
                  iris,
                  show_superclasses=True,
                  show_subclasses=True,
                  language='en',
                  show_table=True):

    """It extracts classes based on give IRIs along with the relations.

    Args:
        source_df (DataFrame): Primary DataFrame to query from.
        iris (list): List of IRIs to query.
        show_superclasses (bool, optional): Flag to extract superclasses.
        Defaults to True.
        show_subclasses (bool, optional): Flag to extract subclasses.
        Defaults to True.
        language (str, optional): Language to query for. Could accept either
        of these: 'en', 'de', and 'fr'.
        Defaults to 'en'.
        show_table (bool, optional): Flag to display the table.
        Defaults to True.

    Returns:
        DataFrame: The DataFrame holding the queried IRIs.
    """

    iris = list(set(iris))

    __validate_args__(arg=iris, flat=False)

    extracted_df = source_df.copy()
    extracted_df = extracted_df[(extracted_df['Language'] == language) &
                                (extracted_df['Superclass language'].isin(
                                    [language, '']))]
    resultant_df = pd.DataFrame()

    for iri in iris:

        class_df = extracted_df.copy()[extracted_df['IRI'] == iri]
        resultant_df = pd.concat([resultant_df, class_df])

        if show_subclasses:
            subclasses_df = extracted_df.copy(
            )[extracted_df['Superclass IRI'] == iri]
            resultant_df = pd.concat([resultant_df, subclasses_df])
        if show_superclasses:
            for _, row in resultant_df['Superclass IRI'].iteritems():
                superclass_df = extracted_df.copy(
                )[extracted_df['IRI'] == row]
                resultant_df = pd.concat([resultant_df, superclass_df])

    resultant_df.sort_values(by=['Label'], inplace=True)
    resultant_df.drop_duplicates(
        subset=['IRI', 'Superclass IRI'], inplace=True)
    resultant_df.drop(['Description (English)',
                       'Description (German)',
                       'Description (French)',
                       'Language',
                       'Superclass language'],
                      axis=1,
                      inplace=True)
    resultant_df.reset_index(drop=True, inplace=True)

    if show_table:
        names = __get_names_from_iris__(iris=iris)

        if len(names) > 1:
            title = 'Class hierarchies of '
        else:
            title = 'Class hierarchy of '
        title += ', '.join(names)

        show(df=resultant_df,
             columnDefs=[ITABLE_COLDEF],
             eval_functions=True,
             tags=ITABLE_TITLE.format(title=title))

    return resultant_df


def get_properties(tenant,
                   username,
                   password,
                   iri,
                   show_table=True,
                   raw=False):

    """It acquires properties for the given IRI.

    Args:
        tenant (string): Tenant id to access API.
        username (string): Username to access API.
        password (string): Password to access API.
        iri (string): The IRI to acquire properties for.
        show_table (bool, optional): Flag for displaying the table.
        Defaults to True.
        raw (bool, optional): Flag to get raw data or its DataFrame.
        Defaults to False.

    Returns:
        DataFrame: The DataFrame holding the properties.
    """

    __validate_args__(arg=iri, flat=True)

    access_token = __get_access_token__(
        tenant=tenant, username=username, password=password)

    url = f'{BASE_URL}{ENAPSO_NAMESPACE}/v1/get-class-own-properties'

    headers = {
        'Content-Type': 'application/json',
        'x-enapso-auth': access_token
    }

    try:
        body = {'cls': iri}
        response = requests.post(
            url=url, headers=headers, json=body, timeout=REQUEST_TIMEOUT)
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
                    compacted_value = PREFIXES.get(prefix)+f":{value.split('#')[1]}"
                    property.update({key: compacted_value})

    properties = pd.DataFrame(data=properties)

    column_display_names = {
        'prop': 'Property',
        'type': 'Type',
        'range': 'Range',
        'max': 'owl:maxCardinality',
        'some': 'owl:someValuesFrom'
    }

    columns = list(properties.columns)
    included_columns = ['prop', 'type', 'range']

    if 'max' in columns:
        included_columns.append('max')
        properties['max'] = properties['max'].fillna('')
    if 'some' in columns:
        included_columns.append('some')
        properties['some'] = properties['some'].fillna('')

    included_column_display_names = {col: column_display_names.get(
        col) for col in included_columns}
    properties = properties[properties.columns[properties.columns.isin(
        included_columns)]]
    properties.rename(columns=included_column_display_names, inplace=True)
    properties.reset_index(drop=True, inplace=True)
    name = __get_name_from_iri__(iri)

    if show_table:
        title=f'Properties of class {name}'

        show(df=properties,
             columnDefs=[ITABLE_COLDEF],
             eval_functions=True,
             tags=ITABLE_TITLE.format(title=title))

    return properties


def get_description(source_df, iris, language='en', show_table=True):

    """It extracts descriptions for the given IRI.

    Args:
        source_df (DataFrame): Primary DataFrame to query from.
        iris (list): IRIs to query description for.
        language (str, optional): Language to query for. Could accept either
        of these: 'en', 'de', and 'fr'.
        Defaults to 'en'.
        show_table (bool, optional): Flag to display the table.
        Defaults to True.

    Returns:
        DataFrame: The DataFrame holding the description of the class.
    """

    iris = list(set(iris))

    __validate_args__(arg=iris, flat=False)

    extracted_df = source_df.copy()
    extracted_df = extracted_df[extracted_df['Language'] == language]
    resultant_df = pd.DataFrame()

    for iri in iris:
        description_df = extracted_df.copy()[extracted_df['IRI'] == iri]
        resultant_df = pd.concat([resultant_df, description_df])

    language_term = LANGUAGE_TERMS.get(language, 'Undefined')

    
    resultant_df.drop_duplicates(subset='IRI', inplace=True)
    resultant_df = resultant_df[resultant_df.columns[resultant_df.columns.isin(
        ['Label', f'Description ({language_term})', f'Definition ({language_term})', f'Example ({language_term})'])]]

    resultant_df.reset_index(drop=True, inplace=True)



    if show_table:
        names = __get_names_from_iris__(iris=iris)

        if len(names) > 1:
            title = 'Description of classes '
        else:
            title = 'Description of class '
        title += ', '.join(names)

        show(df=resultant_df,
             columnDefs=[ITABLE_COLDEF],
             eval_functions=True,
             tags=ITABLE_TITLE.format(title=title))
    print(resultant_df)  # add this line

    return resultant_df


def get_hierarchy_graph(tenant,
                        username,
                        password,
                        source_df,
                        iris,
                        show_superclasses,
                        show_subclasses,
                        language='en',
                        verbose_tooltips=True):

    """It generates a Network object of the class hierarchy for the given
    list of IRIs.

    Args:
        tenant (string): Tenant id to access API.
        username (string): Username to access API.
        password (string): Password to access API.
        source_df (DataFrame): Primary DataFrame to query from.
        iris (list): List of IRIs to query.
        language (str, optional): Language to query for. Could accept either
        of these: 'en', 'de', and 'fr'.
        Defaults to 'en'.
        show_superclasses (bool, optional): Flag to extract superclasses for
        the queried IRIs. Defaults to True.
        show_subclasses (bool, optional): Flag to extract subclasses for the
        queried IRIs. Defaults to True.
        Defaults to 'en'.
        verbose_tooltips (bool, optional): Flag to display extended tooltip.
        Defaults to True.

    Returns:
        Network: The Network object loaded with nodes and edges to display.
    """

    graph = __get_network_graph__(tenant,
                                  username,
                                  password,
                                  source_df,
                                  iris,
                                  show_superclasses=show_superclasses,
                                  show_subclasses=show_subclasses,
                                  show_properties=False,
                                  language=language,
                                  verbose_tooltips=verbose_tooltips)
    return graph


def get_properties_graph(tenant,
                         username,
                         password,
                         source_df,
                         iris,
                         show_superclasses=False,
                         show_subclasses=False,
                         language='en',
                         verbose_tooltips=False):

    """It generates a Network object of the class properties for the given
    list of IRIs.

    Args:
        tenant (string): Tenant id to access API.
        username (string): Username to access API.
        password (string): Password to access API.
        source_df (DataFrame): Primary DataFrame to query from.
        iris (list): List of IRIs to query.
        language (str, optional): Language to query for. Could accept either
        of these: 'en', 'de', and 'fr'.
        Defaults to 'en'.
        show_superclasses (bool, optional): Flag to extract superclasses
        for the queried IRIs. Defaults to True.
        show_subclasses (bool, optional): Flag to extract subclasses for the
        queried IRIs. Defaults to True.
        Defaults to 'en'.
        verbose_tooltips (bool, optional): Flag to display extended tooltip.
        Defaults to True.

    Returns:
        Network: The Network object loaded with nodes and edges to display.
    """

    graph = __get_network_graph__(tenant=tenant,
                                  username=username,
                                  password=password,
                                  source_df=source_df,
                                  iris=iris,
                                  show_superclasses=show_superclasses,
                                  show_subclasses=show_subclasses,
                                  show_properties=True,
                                  language=language,
                                  verbose_tooltips=verbose_tooltips)
    return graph


def __get_network_graph__(tenant,
                          username,
                          password,
                          source_df,
                          iris,
                          show_superclasses=True,
                          show_subclasses=True,
                          show_properties=False,
                          language='en',
                          verbose_tooltips=False):

    iris = list(set(iris))

    __validate_args__(arg=iris, flat=False)

    def tooltip_description(description):

        description_ = ''
        if description:
            line = ''
            count = 0
            added_linebreaks = 0
            for index, char in enumerate(description):
                count += 1
                if count > TOOLTIP_TEXT_MAX_LENGTH + added_linebreaks:
                    description_ += line
                    line = ''
                    description_ = description_[:TOOLTIP_TEXT_MAX_LENGTH+added_linebreaks-1] + '…'
                    break

                line += char
                if (char == '\n'):
                    description_ += line
                    line = ''
                elif len(line) > TOOLTIP_TEXT_WIDTH:
                    linebreak_index = TOOLTIP_TEXT_WIDTH-1
                    for index in range(TOOLTIP_TEXT_WIDTH-1, 0, -1):
                        if line[index].isspace():
                            linebreak_index = index
                            break
                    description_ += line[:linebreak_index+1]+'\n'
                    added_linebreaks += 1
                    line = line[linebreak_index+1:]
            description_ += line + '\n'
            line = ''

        return description_


    def tooltip_properties(properties):
        
        tooltip_ = ''

        for property_type in {'DatatypeProperty','ObjectProperty'}:
            properties_ = properties.get(property_type, '')
            total_number = len(properties_)
            display_number = min(total_number, TOOLTIP_MAX_PROPERTIES)

            if display_number > 0:
                if total_number <= TOOLTIP_MAX_PROPERTIES:
                    if property_type == 'DatatypeProperty':
                        tooltip_ += '\nDatatype properties:\n'
                    elif property_type == 'ObjectProperty':
                        tooltip_ += '\nObject properties:\n'
                else:
                    if property_type == 'DatatypeProperty':
                        tooltip_ += '\nDatatype properties ' + \
                                    f'({display_number}/{total_number}):\n'
                    elif property_type == 'ObjectProperty':
                        tooltip_ += '\nObject properties ' + \
                                    f'({display_number}/{total_number}):\n'

                for index, prop in enumerate(properties_):
                    property_ = __get_name_from_iri__(prop.get('property'))
                    count = index+1

                    if count <= TOOLTIP_MAX_PROPERTIES:
                        tooltip_ += f"• {property_}\n"
                    elif count == TOOLTIP_MAX_PROPERTIES:
                        break
            elif property_type == 'DatatypeProperty':
                tooltip_ += '\nNo datatype properties.\n'
            elif property_type == 'ObjectProperty':
                tooltip_ += '\nNo object properties.\n'

        return tooltip_

    def qualify_class(iri):

        extracted_df = source_df[(source_df['Language'] == language) &
                                 (source_df['Superclass language'].isin(
                                     [language, '']))]
        extracted_df = extracted_df.copy()[extracted_df['IRI'] == iri]
        extracted_df.drop_duplicates(
            subset=['IRI', 'Superclass IRI'], inplace=True)
        if not extracted_df.empty:
            name_or_label = extracted_df['Label'].values[0]
            color = CLASS_COLOR if extracted_df['IsLeafClass'].values[0] \
                else LEAFCLASS_COLOR
        else:
            name_or_label = __get_name_from_iri__(iri)
            color = CLASS_COLOR

        data = {
            'label': name_or_label,
            'color': color,
            'shape': CLASS_SHAPE
        }

        return data

    names = __get_names_from_iris__(iris=iris)

    if show_properties:
        if len(names) > 1:
            title = 'Figure: Properties of classes '
        else:
            title = 'Figure: Properties of class '
    else:
        title = 'Figure: Class hierarchy of '

    title += ', '.join(names)

    # Creating a Network object
    graph = Network(height=GRAPH_HEIGHT, width=GRAPH_WIDTH,
                    directed=True, notebook=True, heading=title)
    graph.repulsion(node_distance=NODE_DISTANCE, spring_length=SPRING_LENGTH)

    # Acquiring required DataFrame
    resultant_df = get_hierarchy(source_df=source_df,
                                 iris=iris,
                                 show_subclasses=show_subclasses,
                                 show_superclasses=show_superclasses,
                                 language=language,
                                 show_table=False)

    # Acquiring descriptions for all classes
    descriptions = __acquire_description__(
        tenant=tenant, username=username, password=password)

    # Forming a dictionary out of involved classes and properties
    nodes = {}
    edges = []
    for _, row in resultant_df.iterrows():
        iri = row.get('IRI')
        superclass_iri = row.get('Superclass IRI')
        description = descriptions.get(iri, {}).get(language, None)

        # Creating edges for properties
        if superclass_iri:
            edge = {
                'parent_node_id': superclass_iri,
                'child_node_id': iri,
                'color': CLASS_EDGE_COLOR
            }
            edges.append(edge)
        # Creating nodes for classes. The key 'reset' indicates that the data
        # for the IRI was populated by an object property, so we need to
        # qualify it.
        if nodes.get(iri, {}).get('reset', True):
            node = {
                'node_id': iri,
                'label': row.get('Label'),
                'tooltip': tooltip_description(description),
                'color': CLASS_COLOR if row.get('IsLeafClass', False)
                else LEAFCLASS_COLOR,
                'shape': CLASS_SHAPE,
                'size': NODE_SIZE,
                'reset': False
            }

            # Larger border width for focus nodes
            if iri in iris:
                node.update({'width': FOCUS_BORDER_WIDTH})

            all_properties = __acquire_properties__(iri=iri,
                                                    tenant=tenant,
                                                    username=username,
                                                    password=password)
            # Adding properties to tooltip
            if verbose_tooltips:
                node.update({'tooltip': node.get('tooltip') +
                            tooltip_properties(all_properties)})

            nodes.update({iri: node})

            # Adding nodes for properties
            if show_properties:
                properties = all_properties.get('DatatypeProperty', [])

                properties += all_properties.get('ObjectProperty', [])

                for property_ in properties:
                    range_ = property_.get('range')
                    if range_ not in nodes:
                        name = __get_name_from_iri__(range_)
                        node = {
                            'node_id': range_,
                            'label': name,
                            'size': NODE_SIZE,
                            'reset': True
                        }

                        # Configuring datatype and object properties differently
                        if property_.get('type') == 'objectproperty':
                            description = descriptions.get(
                                range_, {}).get(language, None)

                            node.update(**qualify_class(iri=range_))
                            node.update(
                                {'tooltip': tooltip_description(description)})

                            if verbose_tooltips:
                                all_properties = __acquire_properties__(
                                    iri=range_,
                                    tenant=tenant,
                                    username=username,
                                    password=password
                                )
                                node.update({'tooltip': node.get(
                                    'tooltip')+'\n'+tooltip_properties(
                                    all_properties)})
                        else:
                            range_ = node.get('node_id')+str(uuid.uuid4())
                            node.update({'node_id': range_})
                            node.update({'color': DATATYPE_NODE_COLOR})
                            node.update({'shape': DATATYPE_NODE_SHAPE})

                        nodes.update({range_: node})

                    # Adding edges for properties
                    name = __get_name_from_iri__(property_.get('property')),
                    edge = {
                        'parent_node_id': range_,
                        'child_node_id': iri,
                        'label': name,
                        'color': PROPERTY_EDGE_COLOR
                    }
                    edges.append(edge)

    # Add nodes to the graph
    for _, value in nodes.items():
        graph.add_node(n_id=value.get('node_id'),
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
            graph.add_edge(to=to,
                             source=source,
                             label=edge.get('label', ' '),
                             color=edge.get('color'),
                             arrowStrikethrough=True)

    return graph
