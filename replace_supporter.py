import re

with open('score_templates/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace CSS
old_css = r'''        .heart-icon \{
            background: #ff66aa;
            border-radius: 50%;
            width: 26px;
            height: 26px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            box-shadow: 0 2px 4px rgba(0,0,0,0\.3);
        \}'''

new_css = '''        .supporter-icon {
            width: 26px;
            height: 26px;
            object-fit: contain;
            filter: drop-shadow(0 1px 3px rgba(0,0,0,0.5));
        }'''

# Replace HTML
old_html = r'''                        \{% if is_supporter %\}
                        <div class="heart-icon">♥</div>
                        \{% endif %\}'''

new_html = '''                        {% if is_supporter %}
                        <img src="{{ assets_dir }}/work/supporter.png" class="supporter-icon" alt="supporter">
                        {% endif %}'''


text = re.sub(old_css, new_css, text)
text = re.sub(old_html, new_html, text)

with open('score_templates/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Replaced!")
