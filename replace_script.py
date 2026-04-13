import re

with open("score_templates/index.html", "r", encoding="utf-8") as f:
    content = f.read()

css_pattern = re.compile(r'\.user-panel \{.*?(?=\.header-right \{)', re.DOTALL)

new_css = """
        .user-panel {
            background-color: rgba(25, 20, 30, 0.6);
            border-radius: 16px;
            display: flex;
            padding: 14px 16px;
            width: 440px;
            height: 130px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
            position: relative;
            overflow: hidden;
            text-shadow: 0px 2px 4px rgba(0,0,0,0.8);
        }
        
        .user-panel-overlay {
            position: absolute;
            inset: 0;
            background: linear-gradient(135deg, rgba(0,0,0,0.3) 0%, rgba(0,0,0,0) 50%, rgba(0,0,0,0.5) 100%);
            z-index: 0;
        }
        
        .user-panel-content {
            position: relative;
            z-index: 1;
            display: flex;
            width: 100%;
            height: 100%;
        }

        .avatar-col {
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 76px;
            margin-right: 16px;
        }
        .avatar {
            width: 70px;
            height: 70px;
            border-radius: 14px;
            object-fit: cover;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }
        
        .rank-labels {
            display: flex;
            flex-direction: column;
            align-items: center;
            font-size: 13px;
            font-weight: 800;
            margin-top: 6px;
            line-height: 1.15;
            letter-spacing: 0.5px;
        }
        
        .global-rank {
            color: #d1c7c7;
        }
        
        .country-rank {
            color: #ffffff;
        }

        .user-details {
            flex: 1;
            display: flex;
            flex-direction: column;
            position: relative;
        }
        
        .username-row {
            font-size: 30px;
            font-weight: 800;
            white-space: nowrap;
            letter-spacing: 0.5px;
            text-overflow: ellipsis;
            overflow: hidden;
            margin-top: -4px;
        }

        .badges-row {
            display: flex;
            gap: 10px;
            align-items: center;
            margin-top: 4px;
        }
        
        .flag-box {
            background: #cd332b;
            padding: 4px 8px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            height: 26px;
            width: 40px;
        }
        .flag {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .heart-icon {
            background: #ff66aa;
            border-radius: 50%;
            width: 26px;
            height: 26px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        
        .user-stats-right {
            position: absolute;
            right: 0;
            bottom: -2px;
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            justify-content: flex-end;
            line-height: 1.25;
        }

        .play-pp {
            font-size: 16px;
            font-weight: 800;
            color: #eeeeee;
            margin-bottom: 2px;
        }

        .level-row {
            font-size: 16px;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: -2px;
            letter-spacing: 0.2px;
        }

        .user-total-pp {
            font-size: 40px;
            font-weight: 800;
            color: #ffffff;
        }

"""

html_pattern = re.compile(r'<div class="header-container">.*?<div class="header-right">', re.DOTALL)

new_html = """<div class="header-container">
        <div class="user-panel" {% if cover_url %}style="background: url('{{ cover_url }}') center/cover no-repeat;"{% endif %}>
            <div class="user-panel-overlay"></div>
            
            <div class="user-panel-content">
                <div class="avatar-col">
                    <img src="{{ avatar_url }}" alt="avatar" class="avatar">
                    <div class="rank-labels">
                        <span class="global-rank">#{{ global_rank }}</span>
                        <span class="country-rank">{{ country_code }}#{{ country_rank }}</span>
                    </div>
                </div>
                
                <div class="user-details">
                    <div class="username-row">{{ user_name }}</div>
                    
                    <div class="badges-row">
                        <div class="flag-box">
                            <img src="{{ flag_url }}" class="flag" alt="flag">
                        </div>
                        {% if is_supporter %}
                        <div class="heart-icon">♥</div>
                        {% endif %}
                    </div>
                    
                    <div class="user-stats-right">
                        <div class="play-pp">+{{ pp }}PP</div>
                        <div class="level-row">{{ hit_accuracy }}% Lv.{{ level }}({{ level_progress }}%)</div>
                        <div class="user-total-pp">{{ user_pp }}PP</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="header-right">"""

content = css_pattern.sub(new_css, content)
content = html_pattern.sub(new_html, content)

with open("score_templates/index.html", "w", encoding="utf-8") as f:
    f.write(content)

print("Replacement done.")
