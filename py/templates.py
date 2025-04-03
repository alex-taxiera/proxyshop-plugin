from functools import cached_property

from src import CFG
import src.helpers as psd
from src.templates import BorderlessVectorTemplate
from src.enums.settings import BorderlessTextbox


class BorderlessIkoriaTemplate(BorderlessVectorTemplate):
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

        # PT Box -> Single static layer
        if self.is_creature and self.pt_group:
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
