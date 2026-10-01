"""
Wagtail hooks for Core app.
Registers custom Draftail features and editor customizations.
"""
import wagtail.admin.rich_text.editors.draftail.features as draftail_features
from wagtail import hooks
from wagtail.admin.rich_text.converters.html_to_contentstate import (
    InlineStyleElementHandler,
    InlineEntityElementHandler,
)
from draftjs_exporter.dom import DOM


@hooks.register("register_rich_text_features")
def register_spoiler_feature(features):
    """
    Register the spoiler inline style feature for Draftail editor.
    
    This creates a Reddit-style spoiler text that:
    - Shows hidden text that reveals on click
    - Stores as <span class="spoiler" data-spoiler="true"> in database
    """
    feature_name = "spoiler"
    type_ = "SPOILER"
    
    # Configure how the feature appears in the Draftail toolbar
    control = {
        "type": type_,
        "label": "👁",
        "description": "Spoiler text (click to reveal)",
        "style": {
            "backgroundColor": "rgba(147, 51, 234, 0.1)",
            "borderBottom": "2px solid rgba(147, 51, 234, 0.5)",
            "borderRadius": "2px",
            "padding": "0 4px",
            "color": "inherit",
        },
    }
    
    # Register the Draftail control
    features.register_editor_plugin(
        "draftail",
        feature_name,
        draftail_features.InlineStyleFeature(control)
    )
    
    # Configure database storage format
    db_conversion = {
        "from_database_format": {
            'span[class="spoiler"]': InlineStyleElementHandler(type_),
        },
        "to_database_format": {
            "style_map": {
                type_: {
                    "element": "span",
                    "props": {
                        "class": "spoiler",
                        "data-spoiler": "true",
                    },
                }
            }
        },
    }
    
    # Register the conversion rules
    features.register_converter_rule(
        "contentstate",
        feature_name,
        db_conversion
    )
    
    # Add spoiler to default features
    features.default_features.append(feature_name)


class CitationEntityElementHandler(InlineEntityElementHandler):
    """
    Custom handler to extract citation data from HTML attributes when loading from database.
    """
    mutability = 'IMMUTABLE'
    
    def get_attribute_data(self, attrs):
        """
        Extract citation data from <a class="citation"> HTML attributes.
        
        Args:
            attrs: Dictionary of HTML attributes from the <a> tag
            
        Returns:
            Dictionary with citation entity data (number, text, url)
        """
        return {
            'number': attrs.get('data-ref', ''),
            'text': attrs.get('data-text', ''),
            'url': attrs.get('data-url', ''),
        }


def citation_entity_decorator(props):
    """
    Convert citation entity from ContentState to HTML.
    
    Creates an anchor tag with citation data attributes and displays
    the citation number in superscript brackets.
    """
    number = props.get('number', '?')
    text = props.get('text', '')
    url = props.get('url', '')
    
    # Build the citation anchor tag
    return DOM.create_element('a', {
        'class': 'citation',
        'data-ref': str(number),
        'data-text': text,
        'data-url': url,
        'href': f'#ref-{number}',
    }, DOM.create_element('sup', {}, f'[{number}]'))


@hooks.register("register_rich_text_features")
def register_citation_feature(features):
    """
    Register the citation entity feature for Draftail editor.
    
    This creates an inline citation that:
    - Displays as a superscript numbered reference [1], [2], etc.
    - Stores citation data (number, text, URL) as entity attributes
    - Renders as <a class="citation"> with data attributes in database
    - Opens a dialog for users to input citation details
    """
    feature_name = "citation"
    type_ = "CITATION"
    
    # Configure how the feature appears in the Draftail toolbar
    control = {
        "type": type_,
        "label": "📖",
        "description": "Add Citation",
        "icon": "📖",
    }
    
    # Register the Draftail control with EntityFeature (not InlineStyleFeature)
    features.register_editor_plugin(
        "draftail",
        feature_name,
        draftail_features.EntityFeature(
            control,
            js=['core/js/citation_plugin.js'],
            css={'all': ['core/css/citation.css']},
        )
    )
    
    # Configure database storage format
    db_conversion = {
        "from_database_format": {
            'a[class="citation"]': CitationEntityElementHandler(type_),
        },
        "to_database_format": {
            "entity_decorators": {
                type_: citation_entity_decorator,
            }
        },
    }
    
    # Register the conversion rules
    features.register_converter_rule(
        "contentstate",
        feature_name,
        db_conversion
    )
    
    # Note: NOT adding to default_features yet - will test first


@hooks.register("insert_editor_css")
def editor_css():
    """
    Load CSS for spoiler styling in the Wagtail editor.
    """
    return '<link rel="stylesheet" href="/static/core/css/spoiler.css">'