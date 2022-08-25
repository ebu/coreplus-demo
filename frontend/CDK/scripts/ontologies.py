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
            raise ValueError('List of IRIs can not be empty or contain an empty string.')
    else:
        if '' == arg:
            raise ValueError('IRI can not be an empty string.')

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
                'Superclass labels': element.get('Label'),
                'Superclass IRIs': element.get('IRI'),
                'Superclass Language': element.get('Language')
            }
            resultant += __flatten__(data=children, parent=_parent)

    return resultant


def __get_access_token__(tenant, username, password):

    url = f'{URL}/auth/realms/{tenant}/protocol/openid-connect/token'

    body = {
        'grant_type': 'password',
        'client_id': 'enapso-sdk',
        'username': username,
        'password': password
    }

    try:
        response = requests.post(url=url, data=body, timeout=300)
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

        response = requests.post(
            url=url, headers=headers, json=body, timeout=300)
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
        response = requests.post(
            url=url, headers=headers, json=body, timeout=300)
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

    for column in list(df.columns):
        df[column] = df[column].fillna('')

    return df


def __extract_labels_from_iris__(iris):

    labels = [iri.split('#')[-1] for iri in iris if iri]

    return labels


def __acquire_properties__(tenant, username, password, iri):

    properties = get_properties(tenant=tenant,
                                username=username,
                                password=password,
                                iri=iri,
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

    url = f'{URL}{INDIVIDUAL_NAMESPACE}/v1/read-individual'

    access_token = __get_access_token__(
        tenant=tenant, username=username, password=password)

    headers = {
        'Content-Type': 'application/json',
        'x-enapso-auth': access_token
    }

    try:
        body = {'cls': iri}
        response = requests.post(
            url=url, headers=headers, json=body, timeout=300)
        response.raise_for_status()
    except requests.exceptions.RequestException as exception:
        return False, str(exception)

    individuals = response.json()
    individuals = individuals.get('records')
    individuals_df = pd.DataFrame(data=individuals)

    label = iri.split('#')[-1]

    alternatives = {
        'iri': 'IRI',
        'alternativeTitle': 'ec:alternativeTitle',
        'contentDescription': 'ec:contentDescription'
    }
    individuals_df.rename(columns=alternatives, inplace=True)

    if show_table:
        show(df=individuals_df,
             columnDefs=[ITABLE_COLDEF],
             eval_functions=True,
             tags=ITABLE_TITLE.format(title=f'Individuals of class {label}'))

    return individuals_df


def load_model(tenant, username, password):

    """It acquires model for the notebook.

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

                    if key == 'en':
                        key = 'English'
                    elif key == 'de':
                        key = 'German'
                    elif key == 'fr':
                        key = 'French'

                    element.update({f'Description({key})': value})

    access_token = __get_access_token__(
        tenant=tenant, username=username, password=password)

    if not access_token:
        return None

    classes = __get_classes__(access_token=access_token)

    __merge_with_descriptions__(classes)

    classes_df = pd.DataFrame(classes)
    classes_df = __remove_nans__(classes_df)

    return classes_df


def get_all_classes(source_df, language='en', show_table=True):

    """It extracts a unique DataFrame of classes from the given DataFrame.

    Args:
        source_df (DataFrame): Primary DataFrame to query from.
        language (str, optional): Language to query for. Could accept either of
        these: 'en', 'de' and 'fr'. Defaults to 'en'.
        show_table (bool, optional): Flag for displaying the table.
        Defaults to True.

    Returns:
        DataFrame: The DataFrame holding the all the classes.
    """

    resultant_df = source_df.copy()
    resultant_df = resultant_df[resultant_df['Language'] == language]
    resultant_df.drop_duplicates(subset='IRI', inplace=True)
    resultant_df = resultant_df[resultant_df.columns[resultant_df.columns.isin(
        ['Label', 'IsLeafClass', 'IRI'])]]
    resultant_df.reset_index(drop=True, inplace=True)

    if show_table:
        show(df=resultant_df,
             columnDefs=[ITABLE_COLDEF],
             eval_functions=True,
             tags=ITABLE_TITLE.format(title=f'List of classes'))

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
        language (str, optional): Language to query for.
        Could accept either of these: 'en', 'de' and 'fr'. Defaults to 'en'.
        show_table (bool, optional): Flag to display the table.
        Defaults to True.

    Returns:
        DataFrame: The DataFrame holding the the queried IRIs.
    """

    iris = list(set(iris))

    __validate_args__(arg=iris, flat=False)

    extracted_df = source_df.copy()
    extracted_df = extracted_df[(extracted_df['Language'] == language) &
                                (extracted_df['Superclass Language'].isin(
                                    [language, '']))]
    resultant_df = pd.DataFrame()

    for iri in iris:

        class_df = extracted_df.copy()[extracted_df['IRI'] == iri]
        resultant_df = pd.concat([resultant_df, class_df])

        if show_subclasses:
            subclasses_df = extracted_df.copy(
            )[extracted_df['Superclass IRIs'] == iri]
            resultant_df = pd.concat([resultant_df, subclasses_df])
        if show_superclasses:
            for _, row in resultant_df['Superclass IRIs'].iteritems():
                superclass_df = extracted_df.copy(
                )[extracted_df['IRI'] == row]
                resultant_df = pd.concat([resultant_df, superclass_df])

    resultant_df.sort_values(by=['Label'], inplace=True)
    resultant_df.drop_duplicates(
        subset=['IRI', 'Superclass IRIs'], inplace=True)
    resultant_df.drop(['Description(French)',
                       'Description(German)',
                       'Description(English)',
                       'Language',
                       'Superclass Language'],
                      axis=1,
                      inplace=True)

    resultant_df.reset_index(drop=True, inplace=True)

    if show_table:
        labels = __extract_labels_from_iris__(iris=iris)
        title = 'Class hierarchy of '+', '.join(labels)

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

    url = f'{URL}{ENAPSO_NAMESPACE}/v1/get-class-own-properties'

    headers = {
        'Content-Type': 'application/json',
        'x-enapso-auth': access_token
    }

    try:
        body = {'cls': iri}
        response = requests.post(
            url=url, headers=headers, json=body, timeout=300)
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

    alternatives = {
        'prop': 'Property',
        'type': 'rdf:type',
        'range': 'rdfs:range',
        'max': 'owl:maxCardinality',
        'some': 'owl:someValuesFrom'
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

    included_alternatives = {col: alternatives.get(
        col) for col in included_columns}
    properties = properties[properties.columns[properties.columns.isin(
        included_columns)]]
    properties.rename(columns=included_alternatives, inplace=True)
    properties.reset_index(drop=True, inplace=True)
    label = iri.split('#')[-1]

    if show_table:
        show(df=properties,
             columnDefs=[ITABLE_COLDEF],
             eval_functions=True,
             tags=ITABLE_TITLE.format(title=f'Properties of class {label}'))

    return properties


def get_description(source_df, iris, language='en', show_table=True):

    """It extracts descriptions for the given IRI.

    Args:
        source_df (DataFrame): Primary DataFrame to query from.
        iris (list): IRIs to query description for.
        language (str, optional): Language to query for. Defaults to 'en'.
        show_table (bool, optional): Flag to display the table.
        Defaults to True.

    Returns:
        DataFrame: The DataFrame holding the the description of class.
    """

    iris = list(set(iris))

    __validate_args__(arg=iris, flat=False)

    extracted_df = source_df.copy()
    extracted_df = extracted_df[extracted_df['Language'] == language]
    resultant_df = pd.DataFrame()

    for iri in iris:
        description_df = extracted_df.copy()[extracted_df['IRI'] == iri]
        resultant_df = pd.concat([resultant_df, description_df])

    language = LANGUAGE_ACRONYMS.get(language, 'Undefined')

    resultant_df.drop_duplicates(subset='IRI', inplace=True)
    resultant_df = resultant_df[resultant_df.columns[resultant_df.columns.isin(
        ['Label', f'Description({language})'])]]
    resultant_df.rename(
        columns={f'Description({language})': 'dcterms:description'},
        inplace=True)
    resultant_df.reset_index(drop=True, inplace=True)

    if show_table:
        labels = __extract_labels_from_iris__(iris=iris)
        title = ', '.join(labels)

        if len(labels) > 1:
            title = f'Description of classes {title}'
        else:
            title = f'Description of class {title}'

        show(df=resultant_df,
             columnDefs=[ITABLE_COLDEF],
             eval_functions=True,
             tags=ITABLE_TITLE.format(title=title))

    return resultant_df


def visualize_hierarchy(tenant,
                        username,
                        password,
                        source_df,
                        iris,
                        language,
                        show_superclasses,
                        show_subclasses,
                        verbose_tooltips=False):

    """It generates a Network object of the hierarchy for the given list of IRIs.

    Args:
        tenant (string): Tenant id to access API.
        username (string): Username to access API.
        password (string): Password to access API.
        source_df (DataFrame): Primary DataFrame to query from.
        iris (list): List of IRIs to query.
        language (str, optional): Language to query for.
        Could accept either of these: 'en', 'de' and 'fr'.
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

    graph = __visualize__(tenant,
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


def visualize_properties(tenant,
                         username,
                         password,
                         source_df,
                         iris,
                         language,
                         show_superclasses=False,
                         show_subclasses=False,
                         verbose_tooltips=False):

    """It generates a Network object of the properties for the given list of IRIs.

    Args:
        tenant (string): Tenant id to access API.
        username (string): Username to access API.
        password (string): Password to access API.
        source_df (DataFrame): Primary DataFrame to query from.
        iris (list): List of IRIs to query.
        language (str, optional): Language to query for. Could accept either of
        these: 'en', 'de' and 'fr'.
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

    graph = __visualize__(tenant=tenant,
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


def __visualize__(tenant,
                  username,
                  password,
                  source_df,
                  iris,
                  show_superclasses=True,
                  show_subclasses=True,
                  show_properties=False,
                  language='en',
                  verbose_tooltips=True):

    iris = list(set(iris))

    __validate_args__(arg=iris, flat=False)

    def format_description(description):

        if description:
            description_ = ''
            for index, char in enumerate(description):
                # Condition is set to display only 200 characters
                if index >= 200:
                    description_ += '...'
                    break
                # Condition is set to add new line after every 50 characters
                elif not (index+1) % 50:
                    description_ += '\n'
                description_ += char
        else:
            description_ = ''

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
                tooltip_ += '...'
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
                tooltip__ += '...'
        tooltip__ = f'\nObject Properties: [{count_}/{len(properties_)}]\n' + \
            tooltip__

        return tooltip_ + tooltip__

    def qualify_class(iri):

        extracted_df = source_df[(source_df['Language'] == language) &
                                 (source_df['Superclass Language'].isin(
                                     [language, '']))]
        extracted_df = extracted_df.copy()[extracted_df['IRI'] == iri]
        extracted_df.drop_duplicates(
            subset=['IRI', 'Superclass IRIs'], inplace=True)
        if not extracted_df.empty:
            label = extracted_df['Label'].values[0]
            color = SUPERCLASS_COLOR if extracted_df['IsLeafClass'].values[0] else SUBCLASS_COLOR
        else:
            label = iri.split('#')[-1]
            color = SUPERCLASS_COLOR

        data = {
            'label': label,
            'color': color,
            'shape': CLASS_SHAPE
        }

        return data

    labels = __extract_labels_from_iris__(iris=iris)

    if show_properties:
        prefix = 'Figure: Properties of class '
        if len(labels) > 1:
            prefix = 'Figure: Properties of classes '
    else:
        prefix = 'Figure: Class hierarchy of '

    title = prefix+', '.join(labels)

    # Creating a Network object
    network = Network(height='800px', width='100%',
                      directed=True, notebook=True, heading=title)
    network.repulsion(node_distance=300, spring_length=300)

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
        # Creating nodes for classes. The key 'reset' indicates that the data
        # for the IRI was populated by an object property, so we need to
        # qualify it.
        if nodes.get(iri, {}).get('reset', True):
            node = {
                'node_id': iri,
                'label': row.get('Label'),
                'tooltip': format_description(description),
                'color': SUPERCLASS_COLOR if row.get('IsLeafClass', False) else SUBCLASS_COLOR,
                'shape': CLASS_SHAPE,
                'size': NODE_SIZE,
                'reset': False
            }

            # Larger width for nodes of focus
            if iri in iris:
                node.update({'width': 4})

            all_properties = __acquire_properties__(iri=iri,
                                                    tenant=tenant,
                                                    username=username,
                                                    password=password)
            # Adding properties to tooltip
            if verbose_tooltips:
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

                        # Configuring datatype and object props differently
                        if property_.get('type') == 'objectproperty':
                            description = descriptions.get(
                                range_, {}).get(language, None)

                            node.update(**qualify_class(iri=range_))
                            node.update(
                                {'tooltip': format_description(description)})

                            if verbose_tooltips:
                                all_properties = __acquire_properties__(
                                    iri=range_,
                                    tenant=tenant,
                                    username=username,
                                    password=password
                                )
                                node.update({'tooltip': node.get(
                                    'tooltip')+format_properties(
                                    all_properties)})
                        else:
                            range_ = node.get('node_id')+str(uuid.uuid4())
                            node.update({'node_id': range_})
                            node.update({'color': DATATYPE_PROPERTY_COLOR})
                            node.update({'shape': DATATYPE_PROPERTY_SHAPE})

                        nodes.update({range_: node})

                    # Adding edge for properties
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

    return network
