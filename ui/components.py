"""
HEM Product Catalogue v3 — Shared UI Components
Reusable widgets: confirm dialogs, thumbnails, stats bar, section headers.
"""
import streamlit as st


# ── Two-step confirmation dialog ──────────────────────────────────────────
def confirm_action(key: str, label: str, message: str, danger: bool = False) -> bool:
    """
    Render a two-step confirm button.
    Returns True only after the user clicks the confirmation 'Yes' button.
    Prevents accidental destructive actions.
    """
    confirm_key = f"_confirm_{key}"
    if confirm_key not in st.session_state:
        st.session_state[confirm_key] = False

    if not st.session_state[confirm_key]:
        # Step 1 — initial button
        if st.button(label, key=key, use_container_width=True):
            st.session_state[confirm_key] = True
            st.rerun()
        return False
    else:
        # Step 2 — show confirmation dialog
        css_cls = "confirm-dialog-danger" if danger else "confirm-dialog"
        st.markdown(f'<div class="{css_cls}">⚠️ {message}</div>', unsafe_allow_html=True)
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("Yes, confirm", key=f"{key}_yes",
                         type="primary", use_container_width=True):
                st.session_state[confirm_key] = False
                return True
        with col_no:
            if st.button("Cancel", key=f"{key}_no", use_container_width=True):
                st.session_state[confirm_key] = False
                st.rerun()
        return False


# ── Product thumbnail ─────────────────────────────────────────────────────
def product_thumbnail_html(image_b64: str, size: int = 38) -> str:
    """Return an <img> or placeholder <div> for a product thumbnail."""
    if image_b64 and len(str(image_b64)) > 100:
        return (
            f'<img src="data:image/jpeg;base64,{image_b64}" '
            f'class="product-thumb" '
            f'style="width:{size}px;height:{size}px;object-fit:cover;" />'
        )
    return (
        f'<div class="product-thumb-placeholder" '
        f'style="width:{size}px;height:{size}px;font-size:9px;">—</div>'
    )


# ── Stats bar ─────────────────────────────────────────────────────────────
def stats_bar(items: list) -> None:
    """
    Render a horizontal dark-gold stats strip.
    items = list of (label, value) tuples.
    """
    spans = "".join(
        f'<span class="stat-item">{lbl}'
        f'<span class="stat-value">{val}</span></span>'
        for lbl, val in items
    )
    st.markdown(f'<div class="stats-bar">{spans}</div>', unsafe_allow_html=True)


# ── Section header ────────────────────────────────────────────────────────
def section_header(text: str, icon: str = "◆") -> None:
    """Render a gold left-bordered section heading."""
    st.markdown(
        f'<div class="section-header">{icon} {text}</div>',
        unsafe_allow_html=True,
    )


# ── Gold horizontal divider ───────────────────────────────────────────────
def gold_divider() -> None:
    """Thin gold gradient divider line."""
    st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)


# ── Empty state placeholder ───────────────────────────────────────────────
def empty_state(icon: str, message: str) -> None:
    """Centered empty-state graphic with icon and message."""
    st.markdown(
        f'<div class="empty-state">'
        f'<div class="empty-state-icon">{icon}</div>'
        f'<p style="color:#60607a;font-size:15px;">{message}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )
