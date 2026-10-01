import wagtail.admin.rich_text.editors.draftail.features as draftail_features
from wagtail import hooks
from wagtail.admin.rich_text.converters.html_to_contentstate import InlineStyleElementHandler


@hooks.register("register_rich_text_features")
def register_spoiler_feature(features):
    """
    Spoiler text for the rich text editor: hidden on the site until clicked.
    Stored as <span class="spoiler" data-spoiler="true">; the frontend adds the behaviour.
    """
    feature_name = "spoiler"
    type_ = "SPOILER"

    control = {
        "type": type_,
        "label": "👁",
        "description": "Spoiler text (click to reveal)",
        # How spoiler text looks inside the editor.
        "style": {
            "backgroundColor": "rgba(147, 51, 234, 0.1)",
            "borderBottom": "2px solid rgba(147, 51, 234, 0.5)",
            "borderRadius": "2px",
            "padding": "0 4px",
            "color": "inherit",
        },
    }
    features.register_editor_plugin(
        "draftail", feature_name, draftail_features.InlineStyleFeature(control)
    )
    features.register_converter_rule(
        "contentstate",
        feature_name,
        {
            "from_database_format": {'span[class="spoiler"]': InlineStyleElementHandler(type_)},
            "to_database_format": {
                "style_map": {
                    type_: {
                        "element": "span",
                        "props": {"class": "spoiler", "data-spoiler": "true"},
                    }
                }
            },
        },
    )
    features.default_features.append(feature_name)
