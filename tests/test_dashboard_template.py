"""Dashboard template shell: Fumadocs Glass layout wiring and theme CSS.

The app template is copied verbatim into every generated dashboard
(`scaffold_app` / `scaffoldApp`), so its structure is part of the generated
output contract. These checks pin the glass theme without building a
dashboard; they also guard the accessibility fallbacks so a future CSS
rewrite cannot silently drop them.
"""

from __future__ import annotations

import unittest

from _support import ROOT

TEMPLATE = ROOT / "skills" / "docforge" / "_shared" / "runtime" / "dashboard" / "template"


class DashboardTemplateTests(unittest.TestCase):
    def test_next_config_is_static_export_ready(self) -> None:
        config = (TEMPLATE / "next.config.mjs").read_text(encoding="utf-8")
        self.assertIn("output: 'export'", config)

    def test_search_route_pre_renders_static_index(self) -> None:
        route = (TEMPLATE / "app" / "api" / "search" / "route.ts").read_text(encoding="utf-8")
        self.assertIn("staticGET", route)
        self.assertIn("export const revalidate = false", route)
        self.assertNotIn("async GET(", route)

    def test_docs_layout_uses_fumadocs_glass_layout(self) -> None:
        layout = (TEMPLATE / "app" / "docs" / "layout.tsx").read_text(encoding="utf-8")
        self.assertIn("fumadocs-ui/layouts/glass", layout)
        self.assertIn("GlassLayout", layout)
        self.assertNotIn("layouts/docs'", layout)

    def test_page_imports_glass_page_components(self) -> None:
        page = (TEMPLATE / "app" / "docs" / "[[...slug]]" / "page.tsx").read_text(encoding="utf-8")
        self.assertIn("fumadocs-ui/layouts/glass/page", page)
        self.assertNotIn("layouts/docs/page", page)

    def test_global_css_imports_glass_stylesheet_in_order(self) -> None:
        css = (TEMPLATE / "app" / "global.css").read_text(encoding="utf-8")
        imports = [
            "@import 'fumadocs-ui/css/generated/glass.css'",
            "@import 'fumadocs-ui/css/neutral.css'",
            "@import 'fumadocs-ui/css/preset.css'",
        ]
        positions = [css.index(value) for value in imports]
        self.assertEqual(positions, sorted(positions), "glass stylesheet must be imported before the preset")

    def test_theme_rounds_corners_beyond_bauhaus_2px(self) -> None:
        css = (TEMPLATE / "app" / "global.css").read_text(encoding="utf-8")
        self.assertNotIn("--radius-xl: 2px", css)
        self.assertIn("--radius-2xl: 1.5rem", css)

    def test_theme_keeps_docforge_red_identity(self) -> None:
        css = (TEMPLATE / "app" / "global.css").read_text(encoding="utf-8")
        self.assertIn("--color-fd-primary: #e30613", css)

    def test_repository_link_uses_native_git_icon(self) -> None:
        shared = (TEMPLATE / "lib" / "layout.shared.tsx").read_text(encoding="utf-8")
        self.assertNotIn("githubUrl", shared)
        self.assertIn("type: 'icon'", shared)
        self.assertIn("GitIcon", shared)
        self.assertNotIn("Github", shared)

    def test_canvas_is_white_in_light_mode(self) -> None:
        css = (TEMPLATE / "app" / "global.css").read_text(encoding="utf-8")
        self.assertIn("--color-fd-background: #ffffff;", css)

    def test_glass_panels_and_ambient_background_present(self) -> None:
        css = (TEMPLATE / "app" / "global.css").read_text(encoding="utf-8")
        self.assertIn("#nd-sidebar", css)
        self.assertIn("--glass-blur", css)
        self.assertIn("--glass-specular", css)
        self.assertIn("backdrop-filter", css)
        self.assertIn("body::before", css)
        self.assertIn("radial-gradient", css)

    def test_light_and_dark_modes_define_complete_glass_materials(self) -> None:
        css = (TEMPLATE / "app" / "global.css").read_text(encoding="utf-8")
        light, dark = css.split(".dark {", maxsplit=1)
        for token in (
            "--glass-fill:",
            "--glass-fill-strong:",
            "--glass-fill-hover:",
            "--glass-border-bright:",
            "--glass-specular:",
            "--glass-highlight:",
            "--glass-blur:",
            "--glass-shadow:",
            "--glass-control-shadow:",
        ):
            self.assertIn(token, light)
            self.assertIn(token, dark)

    def test_glass_controls_have_pointer_feedback(self) -> None:
        css = (TEMPLATE / "app" / "global.css").read_text(encoding="utf-8")
        self.assertIn("button.rounded-full:hover", css)
        self.assertIn("button.rounded-full:active", css)
        self.assertIn("scale(0.97)", css)
        self.assertIn("--glass-pointer-x", css)
        self.assertIn("--glass-caustic", css)

    def test_sidebar_selected_item_is_glass_pill(self) -> None:
        css = (TEMPLATE / "app" / "global.css").read_text(encoding="utf-8")
        self.assertIn("a.rounded-lg.bg-fd-primary\\/10", css)
        self.assertIn("a.rounded-lg:not(.bg-fd-primary\\/10):hover", css)
        self.assertIn("inset-e-0 a.rounded-lg", css)
        self.assertNotIn("liquid-glass-lens", css)

    def test_hybrid_liquid_glass_provider_is_wired(self) -> None:
        layout = (TEMPLATE / "app" / "docs" / "layout.tsx").read_text(encoding="utf-8")
        provider = (TEMPLATE / "components" / "liquid-glass" / "liquid-glass-provider.tsx").read_text(
            encoding="utf-8"
        )
        css = (TEMPLATE / "app" / "global.css").read_text(encoding="utf-8")
        package = (TEMPLATE / "package.json").read_text(encoding="utf-8")
        self.assertIn("LiquidGlassProvider", layout)
        self.assertIn("requestAnimationFrame", provider)
        self.assertIn("prefers-reduced-motion", provider)
        self.assertIn("backdrop-filter", css)
        # The lens is DOM-native: WebGL dependencies would only add weight and
        # framebuffer cost with no correctness benefit for the docs UI.
        self.assertNotIn("getContext('webgl2')", provider)
        self.assertNotIn("@react-three", package)
        self.assertNotIn('"three"', package)
        self.assertNotIn('"maath"', package)
        self.assertNotIn("MeshTransmissionMaterial", css + provider)

    def test_accessibility_fallbacks_present(self) -> None:
        css = (TEMPLATE / "app" / "global.css").read_text(encoding="utf-8")
        for fallback in (
            "@supports not",
            "prefers-reduced-transparency",
            "prefers-reduced-motion",
            "forced-colors",
            "@media print",
        ):
            self.assertIn(fallback, css)


if __name__ == "__main__":
    unittest.main()
