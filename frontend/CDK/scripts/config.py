import os


# Config vars for notebook
NODE_SIZE = 40
CLASS_SHAPE = 'dot'
CLASS_EDGE_COLOR = '#AEB6BF'
DATATYPE_PROPERTY_SHAPE = 'box'
DATATYPE_PROPERTY_COLOR = '#FC3'
ITABLE_SUBCLASS_COLOR = '#7CBC97'
ITABLE_SUPERCLASS_COLOR = '#7DA5C0'
ITABLE_COLDEF = {
    "width": "120px",
    "className": "dt-left",
    "targets": "_all",
    "createdCell": """
        function (td, cellData, rowData, row, col) {{
            $(td).css('word-wrap', 'break-word')
            if (typeof cellData === 'string') {{
                if (cellData.includes('1.0')) {{
                    $(td).html(cellData.replace('.0', '' ))
                }}
            }}
            if (cellData == false) {{
                $(td).css('color', '{superclass_color}')
                $(td).css('font-weight', 'bold')
            }}
            else if (cellData == true) {{
                $(td).css('color', '{subclass_color}')
                $(td).css('font-weight', 'bold')
            }}
        }}
        """.format(superclass_color=ITABLE_SUPERCLASS_COLOR,
                   subclass_color=ITABLE_SUBCLASS_COLOR),
}
SUPERCLASS_COLOR = '#ABEBC6'
SUBCLASS_COLOR = '#ACF'
PROPERTY_EDGE_COLOR = '#000'
FIXED_LEGEND = ('https://image-assets-for-cdk.s3.eu-central-1.amazonaws.com/'
'legend_for_cell.png')
ITABLE_TITLE = ('<h4><label style="font-weight:bold">Table: </label><label>'
'{title}</label></h4>')

# Config vars for APIs
URL = os.getenv('URL', 'https://ebucore-plus-dk.org')
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
