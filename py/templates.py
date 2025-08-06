from functools import cached_property
from typing import Optional, Union, Callable

from photoshop.api._layerSet import LayerSet

from src import CFG
import src.helpers as psd
from src.helpers.effects import apply_fx
from src.templates import BorderlessVectorTemplate
from src.enums.settings import BorderlessTextbox
from src.enums.layers import LAYERS
from src.schema.adobe import EffectStroke


from src.text_layers import FormattedTextArea, TextField
from src.utils.adobe import LayerObjectTypes, ArtLayer

from src.enums.settings import BorderlessColorMode, BorderlessTextbox

# return self.layout.file.get('additional_cfg', {}).get('nick', None)


class BorderlessBorderMod:
    """Borderless Border Mod"""

    """
    * Settings
    """

    @cached_property
    def disable_border(self) -> bool:
        setting = CFG.get_setting("FRAME", "Disable.Border", False)
        override = self.layout.file.get("additional_cfg", {}).get(
            "disable_border", None
        )

        if override is not None:
            return override == "true"

        return setting

    @cached_property
    def border_color(self) -> str:
        """Use 'black' unless an alternate color and a valid border group is provided."""
        if self.disable_border:
            return "black"
        override = self.layout.file.get("additional_cfg", {}).get("border_color", None)
        if override is not None:
            return override
        return super().border_color

    def disable_border_group(self) -> None:
        """Disable the border group if the border is disabled."""
        if self.disable_border:
            self.border_group.visible = False
            apply_fx(self.legal_group, [EffectStroke(weight=7, style="out")])

    @property
    def frame_layer_methods(self) -> list[Callable]:
        return [*super().frame_layer_methods, self.disable_border_group]


class BorderlessIkoriaTemplate(BorderlessBorderMod, BorderlessVectorTemplate):
    template_suffix = "Borderless Ikoria"

    """
    * Settings
    """

    @cached_property
    def color_limit(self) -> int:
        setting = CFG.get_setting(
            section="COLORS", key="Max.Colors", default="2", is_bool=False
        )
        if isinstance(setting, str):
            return int(setting) + 1
        raise ValueError(f"Received invalid value for color limit: {setting}")

    @cached_property
    def front_face_colors(self) -> bool:
        """Returns True if lighter color map should be used on front face DFC cards."""
        return bool(
            CFG.get_setting(section="COLORS", key="Front.Face.Colors", default=True)
        )

    @cached_property
    def multicolor_pinlines(self) -> bool:
        """Returns True if Pinlines for multicolored cards should use blended colors."""
        return bool(
            CFG.get_setting(section="COLORS", key="Multicolor.Pinlines", default=True)
        )

    @cached_property
    def multicolor_pt(self) -> bool:
        """Returns True if PT Box for multicolored cards should use the last color."""
        return bool(
            CFG.get_setting(section="COLORS", key="Multicolor.PT", default=False)
        )

    @cached_property
    def drop_shadow_enabled(self) -> bool:
        """Returns True if Drop Shadow text setting is enabled."""
        return bool(CFG.get_setting(section="TEXT", key="Drop.Shadow", default=True))

    @cached_property
    def crown_texture_enabled(self) -> bool:
        """Returns True if Legendary crown clipping texture should be enabled."""
        return bool(CFG.get_setting(section="FRAME", key="Crown.Texture", default=True))

    @cached_property
    def size(self) -> str:
        """Layer name associated with the size of the textbox."""

        # Check for textless
        if self.is_textless:
            return BorderlessTextbox.Textless

        return BorderlessTextbox.Short

    """
    * Frame Layer Methods
    """

    def enable_frame_layers(self) -> None:
        """Build the card frame by enabling and/or generating various layer."""

        # Enable vector shapes
        self.enable_shape_layers()

        # Enable layer masks
        self.enable_layer_masks()

        print("self.layout", self.layout.scryfall)

        # PT Box -> Single static layer
        if self.is_creature and self.pt_group:
            print("self.pt_colors", self.pt_colors)
            self.pt_group.visible = True
            self.generate_layer(
                group=self.pt_group, colors=self.pt_colors, masks=self.pt_masks
            )

        # Color Indicator -> Blended solid color layers
        if self.is_type_shifted and self.indicator_group:
            self.generate_layer(
                group=self.indicator_group,
                colors=self.indicator_colors,
                masks=self.indicator_masks,
            )

        # Pinlines -> Solid color or gradient layers
        for group in [g for g in self.pinlines_groups if g]:
            group.visible = True
            self.generate_layer(
                group=group, colors=self.pinlines_colors, masks=self.pinlines_masks
            )

        # Twins -> Blended texture layers
        # if self.twins_group:
        #     self.generate_layer(
        #         group=self.twins_group,
        #         colors=self.twins_colors,
        #         masks=self.twins_masks)

        # Textbox -> Blended texture layers
        # if self.textbox_group:
        #     self.generate_layer(
        #         group=self.textbox_group,
        #         colors=self.textbox_colors,
        #         masks=self.textbox_masks)

        # Background layer -> Blended texture layers
        if self.background_group:
            self.generate_layer(
                group=self.background_group,
                colors=self.background_colors,
                masks=self.background_masks,
            )

        # Legendary crown
        if self.is_legendary:
            self.enable_crown()

    """
    * Post Text Methods
    """

    def nickname_adjustments(self) -> None:
        """Actions taken if this is a 'Nickname' render."""

        # Nickname plate -> Solid color or gradient layer
        # if self.is_nickname:
        #     self.generate_layer(
        #         group=self.nickname_group,
        #         colors=self.twins_colors)

        # Center the name
        psd.align_vertical(self.text_layer_name, self.nickname_shape)

        # Copy effects to legendary crown
        if self.is_legendary:
            psd.copy_layer_fx(self.nickname_fx, self.crown_group.parent)

class BorderlessShowcaseFCATemplate(BorderlessBorderMod, BorderlessVectorTemplate):
    template_suffix = "Borderless Showcase, FCA"

    @cached_property
    def drop_shadow_enabled(self) -> bool:
        return False


    @cached_property
    def size(self) -> str:
        """Layer name associated with the size of the textbox."""

        # Check for textless
        if self.is_textless:
            return BorderlessTextbox.Textless

        return BorderlessTextbox.Tall

    def rules_text_and_pt_layers(self) -> None:
        """Add rules and power/toughness text."""
        self.text.extend([
            FormattedTextArea(
                layer=self.text_layer_rules,
                contents=self.layout.oracle_text,
                flavor=self.layout.flavor_text,
                reference=self.textbox_reference,
                divider=self.divider_layer,
                pt_reference=self.pt_reference,
                centered=False,
                vertically_centered=False
            ),
            TextField(
                layer=self.text_layer_pt,
                contents=f"{self.layout.power}/{self.layout.toughness}"
            ) if self.is_creature else None
        ])

    def format_nickname_text(self) -> None:
        # Center the card name on the nickname plate
        psd.align_left(self.text_layer_name, self.text_layer_nickname)

    @cached_property
    def enabled_shapes(self) -> list[Union[ArtLayer, LayerSet, None]]:
        """Vector shapes that should be enabled during the enable_shape_layers step. Should be
            a list of layer, layer group, or None objects."""
        return [self.border_shape]


    def enable_frame_layers(self) -> None:
        """Build the card frame by enabling and/or generating various layer."""

        # Enable vector shapes
        self.enable_shape_layers()

        # Enable layer masks
        self.enable_layer_masks()

        # PT Box -> Single static layer
        # if self.is_creature and self.pt_group:
        #     self.pt_group.visible = True
        #     self.generate_layer(
        #         group=self.pt_group,
        #         colors=self.pt_colors,
        #         masks=self.pt_masks)

        # Color Indicator -> Blended solid color layers
        if self.is_type_shifted and self.indicator_group:
            self.generate_layer(
                group=self.indicator_group,
                colors=self.indicator_colors,
                masks=self.indicator_masks)

        # Pinlines -> Solid color or gradient layers
        # for group in [g for g in self.pinlines_groups if g]:
        #     group.visible = True
        #     self.generate_layer(
        #         group=group,
        #         colors=self.pinlines_colors,
        #         masks=self.pinlines_masks)

        # Twins -> Blended texture layers
        # if self.twins_group:
        #     self.generate_layer(
        #         group=self.twins_group,
        #         colors=self.twins_colors,
        #         masks=self.twins_masks)

        # Textbox -> Blended texture layers
        # if self.textbox_group:
        #     self.generate_layer(
        #         group=self.textbox_group,
        #         colors=self.textbox_colors,
        #         masks=self.textbox_masks)

        # Background layer -> Blended texture layers
        if self.background_group:
            self.generate_layer(
                group=self.background_group,
                colors=self.background_colors,
                masks=self.background_masks)

        # Legendary crown
        # if self.is_legendary:
        #     self.enable_crown()


class BorderlessModernTemplate(BorderlessBorderMod, BorderlessVectorTemplate):
    template_suffix = "Borderless Modern"

    dark_bg = "#0D0D0D"

    # pinlines_color_map = {
    #     # Default pinline colors
    #     'W': [246, 246, 239],
    #     'U': [0, 117, 190],
    #     'B': [56, 54, 48],
    #     'R': [239, 56, 39],
    #     'G': [11, 116, 70],
    #     'Gold': [233, 199, 72],
    #     'Land': [165, 147, 133],
    #     'Artifact': [138, 159, 173],
    #     'Colorless': [230, 236, 242],
    #     'Vehicle': [77, 45, 5]
    # }

    pinlines_color_map = {
        "W": "#F6F6EF",
        "U": "#0075be",
        "B": "#383630",
        "R": "#ef3827",
        "G": "#0b7446",
        "Gold": "#e9c748",
        "Land": "#a59385",
        "Artifact": "#8a9fad",
        "Colorless": "#E6ECF2",
        "Vehicle": "#4D2D05",
    }

    # twins_color_map = {
    #     # Default twins colors
    #     'W': [246, 246, 239],
    #     'U': [0, 117, 190],
    #     'B': [56, 54, 48],
    #     'R': [239, 56, 39],
    #     'G': [11, 116, 70],
    #     'Gold': [233, 199, 72],
    #     'Land': [165, 147, 133],
    #     'Artifact': [138, 159, 173],
    #     'Colorless': [230, 236, 242],
    #     'Vehicle': [77, 45, 5]
    # }

    twins_color_map = {
        "W": "#878377",
        "U": "#0075be",
        "B": "#383630",
        "R": "#b82e1c",
        "G": "#1f593f",
        "Gold": "#94762f",
        "Land": "#8f8c88",
        "Artifact": "#8a9fad",
        "Colorless": "#E6ECF2",
        "Vehicle": "#4D2D05",
    }

    dual_land_color = "#85817e"
    # * Multicolor nameplate fill note: *I use slightly different colors for different card types, but what this really strongly depends on is the background (art) color, so I'll list them in order of preference for all purposes but also state what card type I commonly use them for below the first choice.*
    # * Multicolor All-Card-Type Recommended Default: #94762f
    # * Multicolor Creature: #9e7939
    # * Multicolor Land: #9e822f
    # * Multicolor Other: #9b822a
    # * Black: #282523 — *perhaps consider lowering the opacity of the nameplate for this one color identity to 60%*

    dark_twins_color_map = {
        "W": "#878377",
        "U": "#036cad",
        "B": "#383630",
        "R": "#972122",
        "G": "#15543a",
        "Gold": "#94762f",
        "Land": "#878480",
        "Artifact": "#8a9fad",
        "Colorless": "#E6ECF2",
        "Vehicle": "#4D2D05",
    }

    @cached_property
    def pt_pinlines_color_map(self) -> dict[str, str]:
        return {
            **self.pinlines_color_map.copy(),
            "B": "#292622",
        }

    pt_fill_color_map = {
        "W": "#8f8071",
        "U": "#1e5576",
        "B": "#3c342c",
        "R": "#972122",
        "G": "#185231",
        "Gold": "#87693f",
        "Artifact": "#365d6b",
        "Colorless": "#A7C6ED",
        "Vehicle": "#4f6066",
    }

    @cached_property
    def crown_color_map(self) -> dict:
        """Maps color values for the Legendary Crown."""
        return {
            **super().crown_color_map,
            "U": "#116cad",
            "Artifact": "#a3b6bf",
        }

    @cached_property
    def drop_shadow_enabled(self) -> bool:
        return False

    @cached_property
    def textbox_colors(self):
        if self.is_land:
            return psd.get_pinline_gradient(
                colors=self.twins,
                color_map=self.dark_color_map,
                location_map=self.gradient_location_map,
            )

        return self.dark_bg

    @cached_property
    def twins_colors(self) -> Union[list[int], list[dict]]:

        # Default to twins
        colors = self.twins

        # Color enabled hybrid OR color enabled multicolor
        if (self.is_hybrid and self.hybrid_colored) or (
            self.is_multicolor and self.multicolor_twins
        ):
            colors = self.identity
        # Color disabled hybrid cards
        elif self.is_hybrid:
            colors = LAYERS.HYBRID

        # Use artifact twins if artifact mode isn't colored
        if (
            self.is_artifact
            and not self.is_land
            and self.artifact_color_mode
            not in [
                BorderlessColorMode.Twins_And_PT,
                BorderlessColorMode.Twins,
                BorderlessColorMode.All,
            ]
        ):
            colors = LAYERS.ARTIFACT

        # Return Solid Color or Gradient notation
        return psd.get_pinline_gradient(
            colors=colors,
            color_map=self.pinlines_color_map,
            location_map=self.gradient_location_map,
        )

    @cached_property
    def pt_colors(self):

        # Default to twins, or Vehicle for non-colored vehicle artifacts
        colors = self.twins

        # Color enabled hybrid OR color enabled multicolor
        if (self.is_hybrid and self.hybrid_colored) or (
            self.is_multicolor and self.multicolor_pt
        ):
            colors = self.identity[-1]
        # Use Hybrid color for color-disabled hybrid cards
        elif self.is_hybrid:
            colors = LAYERS.HYBRID

        # Use artifact twins color if artifact mode isn't colored
        if (
            self.is_artifact
            and not self.is_land
            and self.artifact_color_mode
            not in [
                BorderlessColorMode.Twins_And_PT,
                BorderlessColorMode.All,
                BorderlessColorMode.PT,
            ]
        ):
            colors = LAYERS.ARTIFACT

        # Use Vehicle for non-colored artifacts
        if colors == LAYERS.ARTIFACT and self.is_vehicle:
            colors = LAYERS.VEHICLE

        return colors

    @cached_property
    def pt_outer_colors(self) -> Union[list[int], list[dict]]:
        # Return Solid Color or Gradient notation
        return psd.get_pinline_gradient(
            colors=self.pt_colors, color_map=self.pt_pinlines_color_map
        )

    @cached_property
    def pt_inner_colors(self) -> Union[list[int], list[dict]]:
        # Return Solid Color or Gradient notation
        return self.pt_fill_color_map[self.pt_colors]

    @cached_property
    def card_name_group(self) -> Optional[LayerSet]:
        return psd.getLayerSet(LAYERS.NAME, self.twins_group)

    @cached_property
    def typeline_group(self) -> Optional[LayerSet]:
        return psd.getLayerSet(LAYERS.TYPE_LINE, self.twins_group)

    @cached_property
    def pt_inner_group(self) -> Optional[LayerSet]:
        return psd.getLayerSet("Inner", [self.pt_group, LAYERS.SHAPE])

    @cached_property
    def pt_outer_group(self) -> Optional[LayerSet]:
        return psd.getLayerSet("Outer", [self.pt_group, LAYERS.SHAPE])

    @cached_property
    def twins_shape(self) -> Union[LayerObjectTypes, list[LayerObjectTypes], None]:
        """Separate shapes for Name and Typeline box."""
        return [
            psd.getLayer(
                (
                    LAYERS.TRANSFORM
                    if self.is_transform or self.is_mdfc
                    else LAYERS.NORMAL
                ),
                [self.twins_group, LAYERS.NAME, LAYERS.SHAPE],
            ),
            psd.getLayer(
                LAYERS.TEXTLESS if self.is_textless else self.size,
                [self.twins_group, LAYERS.TYPE_LINE, LAYERS.SHAPE],
            ),
        ]

    @cached_property
    def crown_shape(self) -> Optional[LayerSet]:
        """Vector shape for Legendary Crown."""
        if not self.is_legendary or not self.is_nickname: # Only return if Legendary and Nickname
            return None
        return psd.getLayerSet(
            LAYERS.NICKNAME,
            [self.crown_group, LAYERS.SHAPE]
        )

    def enable_frame_layers(self) -> None:
        """Build the card frame by enabling and/or generating various layer."""

        # Enable vector shapes
        self.enable_shape_layers()

        # Enable layer masks
        self.enable_layer_masks()

        # PT Box -> inner and outer
        if self.is_creature and self.pt_group:
            self.pt_group.visible = True
            if self.pt_inner_group:
                self.generate_layer(
                    group=self.pt_inner_group,
                    colors=self.pt_inner_colors,
                    masks=self.pt_masks,
                )

            if self.pt_outer_group:
                self.generate_layer(
                    group=self.pt_outer_group,
                    colors=self.pt_outer_colors,
                    masks=self.pt_masks,
                )

        # Color Indicator -> Blended solid color layers
        if self.is_type_shifted and self.indicator_group:
            self.generate_layer(
                group=self.indicator_group,
                colors=self.indicator_colors,
                masks=self.indicator_masks,
            )

        # Pinlines -> Solid color or gradient layers
        for group in [g for g in self.pinlines_groups if g]:
            group.visible = True
            self.generate_layer(
                group=group, colors=self.pinlines_colors, masks=self.pinlines_masks
            )

        # Twins -> Blended texture layers
        if self.card_name_group:
            self.generate_layer(
                group=self.card_name_group,
                colors=self.twins_colors,
                masks=self.twins_masks,
            )

        if self.typeline_group:
            self.generate_layer(
                group=self.typeline_group,
                colors=self.twins_colors if self.is_land else self.dark_bg,
                masks=self.twins_masks,
            )

        # Textbox -> Blended texture layers
        if self.textbox_group:
            self.generate_layer(
                group=self.textbox_group,
                colors=self.textbox_colors,
                masks=self.textbox_masks,
            )

        # Background layer -> Blended texture layers
        if self.background_group:
            self.generate_layer(
                group=self.background_group,
                colors=self.background_colors,
                masks=self.background_masks,
            )

        # Legendary crown
        if self.is_legendary:
            self.enable_crown()

        # Color the nickname plate if enabled in settings
        if self.is_nickname and self.is_colored_nickname:
            self.generate_layer(group=self.nickname_group, colors=self.twins_colors)
