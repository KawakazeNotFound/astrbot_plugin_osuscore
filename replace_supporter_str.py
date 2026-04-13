import sys

with open('score_templates/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

old_css = """        .heart-icon {
            background: #ff66aa;
            border-radius: 50%;
            width: 26px;
            height: 26px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }"""

new_css = """        .supporter-icon {
            width: 26px;
            height: 26px;
            object-fit: contain;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
        }"""

text = text.replace(old_css, new_css)

old_html = """                        {% if is_supporter %}
                        <div class="heart-icon">♥</div>
                        {% endif %}"""

new_html = """                        {% if is_supporter %}
                        <img src="{{ assets_dir }}/work/supporter.png" class="supporter-icon" alt="supporter">
                        {% endif %}"""

text = text.replace(old_html, new_html)

with open('score_templates/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Replaced with str.replace!")
