"""
Wagtail hooks for Core app.
Registers custom Draftail features and editor customizations.
"""
import wagtail.admin.rich_text.editors.draftail.features as draftail_features
from wagtail import hooks
from wagtail.admin.rich_text.converters.html_to_contentstate import (
    InlineStyleElementHandler,
)


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


@hooks.register("insert_editor_css")
def editor_css():
    """
    Load CSS for spoiler styling in the Wagtail editor.
    """
    return '<link rel="stylesheet" href="/static/core/css/spoiler.css">'