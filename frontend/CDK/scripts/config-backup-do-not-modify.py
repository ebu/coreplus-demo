import os


# Config vars for notebook
NODE_SIZE = 40
CLASS_SHAPE = 'dot'
CLASS_COLOR = '#ABEBC6'
CLASS_EDGE_COLOR = '#AEB6BF'
LEAFCLASS_COLOR = '#ACF'
PROPERTY_EDGE_COLOR = '#000'
DATATYPE_NODE_SHAPE = 'box'
DATATYPE_NODE_COLOR = '#FC3'
FOCUS_BORDER_WIDTH = 4
NODE_DISTANCE = 300
SPRING_LENGTH = 300
GRAPH_HEIGHT = '800px'
GRAPH_WIDTH = '100%'
TOOLTIP_TEXT_MAX_LENGTH = 600
TOOLTIP_TEXT_WIDTH = 100
TOOLTIP_MAX_PROPERTIES = 3
TOOLTIP_MAX_PROPERTIES = 3
# LEGEND_URL = ('https://image-assets-for-cdk.s3.eu-central-1.amazonaws.com/'
# 'legend_for_cell.png')

ITABLE_CLASS_COLOR = '#7DA5C0'
ITABLE_LEAFCLASS_COLOR = '#7CBC97'
ITABLE_TITLE = ('<h4><label style="font-weight:bold">Table: </label><label>'
'{title}</label></h4>')
ITABLE_COLDEF = {
    "width": "120px",
    "className": "dt-left",
    "targets": "_all",
    "createdCell": """
        function (td, cellData, rowData, row, col) {{
            $(td).css('word-wrap', 'break-word')
            if (typeof cellData === 'string') {{
                if (cellData.includes('.0')) {{
                    $(td).html(cellData.replace('.0', '' ))
                }}
            }}
            if (cellData == false) {{
                $(td).css('color', '{class_color}')
                $(td).css('font-weight', 'bold')
            }}
            else if (cellData == true) {{
                $(td).css('color', '{leafclass_color}')
                $(td).css('font-weight', 'bold')
            }}
        }}
        """.format(class_color=ITABLE_CLASS_COLOR,
                   leafclass_color=ITABLE_LEAFCLASS_COLOR),
}

# Config vars for APIs
BASE_URL = os.getenv('URL', 'https://ebucore-plus-dk.org')
BASE_URL = os.getenv('BASE_URL', BASE_URL)
SOURCE_GRAPH = 'http://www.ebu.ch/metadata/ontologies/ebucore'
ENAPSO_NAMESPACE = '/enapso-dev/ontology-management'
INDIVIDUAL_NAMESPACE = '/enapso-dev/individual-management'
REQUEST_TIMEOUT = 300

# Config vars for data
LANGUAGES = ['en', 'de', 'fr']
LANGUAGE_TERMS = {
    'en': 'English',
    'de': 'German',
    'fr': 'French'
}
PREFIXES = {
    'http://creativecommons.org/ns#': 'cc',
    'http://purl.org/dc/elements/1.1/': 'dc',
    'http://purl.org/dc/terms/': 'dcterms',
    'http://purl.org/vocab/vann/': 'vann',
    'http://spinrdf.org/spin#': 'spin',
    'http://www.ebu.ch/metadata/ontologies/ebuccdm#': 'ebuccdm',
    'http://www.ebu.ch/metadata/ontologies/ebucore/ebucore#': 'ec',
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#': 'rdf',
    'http://www.w3.org/2000/01/rdf-schema#': 'rdfs',
    'http://www.w3.org/2001/XMLSchema#': 'xsd',
    'http://www.w3.org/2002/07/owl#': 'owl',
    'http://www.w3.org/2003/06/sw-vocab-status/ns#': 'vs',
    'http://www.w3.org/2004/02/skos/core#': 'skos',
    'http://www.w3.org/2006/time#': 'time',
    'http://www.w3.org/XML/1998/namespace': 'xml'
}
