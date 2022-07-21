import os


# Config vars for notebook
NODE_SIZE = 40
CLASS_SHAPE = 'dot'
CLASS_EDGE_COLOR = '#AEB6BF'
DATATYPE_PROPERTY_SHAPE = 'box'
DATATYPE_PROPERTY_COLOR = '#FC3'
ITABLE_SUBCLASS_COLOR = '#7DA5C0'
ITABLE_SUPERCLASS_COLOR = '#7CBC97'
ITABLE_COLDEF = {
    "width": "120px",
    "className": "dt-center",
    "targets": "_all",
    "createdCell": """
        function (td, cellData, rowData, row, col) {{
            $(td).css('word-wrap', 'break-word')
            if (cellData == false) {{
                $(td).css('color', '{superclass_color}')
                $(td).css('font-weight', 'bold')
                $(td).html = "False"
            }}
            else if (cellData == true) {{
                $(td).css('color', '{subclass_color}')
                $(td).css('font-weight', 'bold')
                $(td).html = "True"
            }}
        }}
        """.format(superclass_color=ITABLE_SUPERCLASS_COLOR,
                   subclass_color=ITABLE_SUBCLASS_COLOR),
}
SUPERCLASS_COLOR = '#ACF'
SUBCLASS_COLOR = '#ABEBC6'
PROPERTY_EDGE_COLOR = '#000'
FULL_LEGEND = 'https://res.cloudinary.com/alieymsxxn/image/upload/v1655326290/legend_full_new_kaewdm.gif'
SHORT_LEGEND = 'https://res.cloudinary.com/alieymsxxn/image/upload/v1655326772/legend_short_final_cki45k.gif'
ITABLE_TITLE = '<h4 style="text-alignt:center"><label style="font-weight:bold">Table: </label><label>{title}</label></h4>'

# Config vars for APIs
URL = os.getenv('URL')
ENAPSO_NAMESPACE = '/enapso-dev/ontology-management'
GRAPH = 'http://www.ebu.ch/metadata/ontologies/ebucore'
INDIVIDUAL_NAMESPACE = '/enapso-dev/individual-management'

# Other config vars
LANGUAGE_ACRONYMS = {
    'en': 'English',
    'de': 'German',
    'fr': 'French'
}
PREFIXES = {
    'http://spinrdf.org/spin#': 'spin',
    'http://purl.org/dc/terms/': 'terms',
    'http://purl.org/vocab/vann/': 'vann',
    'http://purl.org/dc/terms/': 'dcterms',
    'http://creativecommons.org/ns#': 'cc',
    'http://www.w3.org/2006/time#': 'time',
    'http://www.w3.org/2002/07/owl#': 'owl',
    'http://purl.org/dc/elements/1.1/': 'dc',
    'http://www.w3.org/2001/XMLSchema#': 'xsd',
    'http://www.w3.org/XML/1998/namespace': 'xml',
    'http://www.w3.org/2004/02/skos/core#': 'skos',
    'http://www.w3.org/2000/01/rdf-schema#': 'rdfs',
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#': 'rdf',
    'http://www.w3.org/2003/06/sw-vocab-status/ns#': 'vs',
    'http://www.ebu.ch/metadata/ontologies/ebucore/ebucore#': ' ',
    'http://www.ebu.ch/metadata/ontologies/ebuccdm#': 'ebuccdm',
    'http://www.ebu.ch/metadata/ontologies/ebucore/ebucore#': 'ec'
}
