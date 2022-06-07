BASE_URL = 'https://ebu-cdk.innotrade.com'
DEMO_TENANT_ID = 'Demo-UUID'
NAMESPACE = '/enapso-dev/ontology-management'
INDIVIDUAL_NAMESPACE = '/enapso-dev/individual-management'
EBUCORE_GRAPH = 'http://www.ebu.ch/metadata/ontologies/ebucore'

ITABLE_COLDEF = {  
                "width": "120px",
                "className": "dt-center",
                "targets": "_all",
                "createdCell": """
                    function (td, cellData, rowData, row, col) {
                        $(td).css('word-wrap', 'break-word')
                        if (cellData == false) {
                            $(td).css('color', '#7da5c0')
                            $(td).css('font-weight', 'bold')
                            $(td).html = "False"
                        }
                        else if (cellData == true) {
                            $(td).css('color', '#7cbc97')
                            $(td).css('font-weight', 'bold')
                            $(td).html = "True"
                        }
                    }
                    """,
                }
ITABLE_TITLE = '<h4 style="text-alignt:center"><label style="font-weight:bold">Table: </label><label>{title}</label></h4>'

PREFIXES = {
    'http://www.ebu.ch/metadata/ontologies/ebucore/ebucore#': ' ',
    'http://creativecommons.org/ns#': 'cc',
    'http://purl.org/dc/elements/1.1/': 'dc', 
    'http://www.ebu.ch/metadata/ontologies/ebucore/ebucore#': 'ec',
    'http://www.w3.org/2003/06/sw-vocab-status/ns#': 'vs',
    'http://www.w3.org/2002/07/owl#': 'owl',
    'http://www.w3.org/1999/02/22-rdf-syntax-ns#':'rdf',
    'http://www.w3.org/XML/1998/namespace': 'xml',
    'http://www.w3.org/2001/XMLSchema#': 'xsd',
    'http://www.w3.org/2000/01/rdf-schema#': 'rdfs',
    'http://www.w3.org/2004/02/skos/core#': 'skos',
    'http://spinrdf.org/spin#': 'spin',
    'http://www.w3.org/2006/time#': 'time',
    'http://purl.org/vocab/vann/': 'vann',
    'http://purl.org/dc/terms/': 'terms',
    'http://purl.org/dc/terms/': 'dcterms',
    'http://www.ebu.ch/metadata/ontologies/ebuccdm#': 'ebuccdm'
}