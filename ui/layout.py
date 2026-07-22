import streamlit as st


def hero_section(
    title: str,
    subtitle: str,
    description: str,
    button_text: str = None,
    button_key: str = None,
):
    st.markdown(
        f"""
        <div class="hero-shell">
            <div class="hero-copy">
                <div class="eyebrow">AI Digital Auditor</div>
                <h1>{title}</h1>
                <p class="hero-lead">{subtitle}</p>
                <div class="hero-description">{description}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if button_text:
        if st.button(button_text, key=button_key, use_container_width=True):
            return True

    return False


def glass_panel(title: str, body: str, footer: str = None):
    html = [
        '<div class="glass-panel">',
        f'  <div class="glass-panel-title">{title}</div>',
        f'  <div class="glass-panel-body">{body}</div>',
    ]

    if footer:
        html.append(f'  <div class="glass-panel-footer">{footer}</div>')

    html.append('</div>')

    st.markdown("""\n""".join(html), unsafe_allow_html=True)


def feature_grid(rows):
    content = ["<div class=\"feature-grid\">"]

    for item in rows:
        content.append(
            f"<div class=\"feature-card\"><h3>{item['title']}</h3><p>{item['description']}</p></div>"
        )

    content.append("</div>")
    st.markdown("""\n""".join(content), unsafe_allow_html=True)
