Update news · PY
Copy

#!/usr/bin/env python3
"""
AI News Portal - Daily Update Script
Fetches latest AI news using Claude API with web search,
scores by importance criteria, and updates index.html
"""

import anthropic
import json
import re
from datetime import datetime

# HTML template with placeholder for news data
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Organizational AI Radar - News Ranked by Importance</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: #000; color: #e2e8f0; min-height: 100vh; line-height: 1.6; }
        .bg-glow { position: fixed; inset: 0; overflow: hidden; pointer-events: none; z-index: 0; }
        .bg-glow::before { content: ''; position: absolute; top: -400px; right: -400px; width: 800px; height: 800px; background: rgba(79, 70, 229, 0.1); border-radius: 50%; filter: blur(100px); }
        .bg-glow::after { content: ''; position: absolute; bottom: -300px; left: -300px; width: 600px; height: 600px; background: rgba(139, 92, 246, 0.1); border-radius: 50%; filter: blur(100px); }
        .grid-overlay { position: fixed; inset: 0; opacity: 0.05; pointer-events: none; background-image: linear-gradient(rgba(99, 102, 241, 0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(99, 102, 241, 0.3) 1px, transparent 1px); background-size: 80px 80px; }
        .container { position: relative; z-index: 10; }
        header { position: sticky; top: 0; z-index: 20; background: rgba(0, 0, 0, 0.8); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
        .header-inner { max-width: 900px; margin: 0 auto; padding: 1.25rem 1.5rem; display: flex; align-items: center; justify-content: space-between; }
        .logo-section { display: flex; align-items: center; gap: 1rem; }
        .logo-icon { width: 40px; height: 40px; border-radius: 12px; background: linear-gradient(135deg, #6366f1, #8b5cf6, #a855f7); display: flex; align-items: center; justify-content: center; box-shadow: 0 8px 20px rgba(99, 102, 241, 0.3); }
        .logo-icon svg { width: 20px; height: 20px; color: white; }
        .logo-text h1 { font-size: 1.125rem; font-weight: 600; color: white; }
        .logo-text h1 span { background: linear-gradient(135deg, #818cf8, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .logo-text p { font-size: 0.75rem; color: #64748b; }
        .scoring-legend { max-width: 900px; margin: 0 auto; padding: 1rem 1.5rem; }
        .scoring-box { background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 1rem; }
        .scoring-title { font-size: 0.7rem; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.75rem; }
        .scoring-items { display: flex; flex-wrap: wrap; gap: 1rem; }
        .scoring-item { display: flex; align-items: center; gap: 0.5rem; font-size: 0.75rem; position: relative; cursor: help; }
        .scoring-item .tooltip { position: absolute; bottom: 100%; left: 50%; transform: translateX(-50%); margin-bottom: 8px; padding: 0.75rem 1rem; background: #1e293b; border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; font-size: 0.75rem; color: #e2e8f0; width: 280px; opacity: 0; visibility: hidden; transition: all 0.2s; z-index: 100; box-shadow: 0 10px 30px rgba(0,0,0,0.5); line-height: 1.5; }
        .scoring-item .tooltip::after { content: ''; position: absolute; top: 100%; left: 50%; transform: translateX(-50%); border: 6px solid transparent; border-top-color: #1e293b; }
        .scoring-item:hover .tooltip { opacity: 1; visibility: visible; }
        .tooltip-title { font-weight: 600; color: white; margin-bottom: 0.25rem; }
        .tooltip-question { color: #94a3b8; font-style: italic; }
        .scoring-dot { width: 8px; height: 8px; border-radius: 50%; }
        .scoring-dot.cap { background: #8b5cf6; }
        .scoring-dot.eco { background: #10b981; }
        .scoring-dot.irr { background: #f59e0b; }
        .scoring-dot.tml { background: #06b6d4; }
        .scoring-dot.sys { background: #f43f5e; }
        .scoring-label.cap { color: #a78bfa; }
        .scoring-label.eco { color: #34d399; }
        .scoring-label.irr { color: #fbbf24; }
        .scoring-label.tml { color: #22d3ee; }
        .scoring-label.sys { color: #fb7185; }
        .scoring-weight { color: #475569; }
        main { max-width: 900px; margin: 0 auto; padding: 0 1.5rem 2rem; }
        .news-list { display: flex; flex-direction: column; gap: 1rem; }
        .news-card { background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 16px; padding: 1.5rem; transition: all 0.3s; }
        .news-card:hover { background: rgba(255, 255, 255, 0.04); border-color: rgba(255, 255, 255, 0.1); }
        .news-inner { display: flex; gap: 1.25rem; }
        .news-rank { flex-shrink: 0; width: 56px; height: 56px; background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.2)); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 12px; display: flex; flex-direction: column; align-items: center; justify-content: center; }
        .news-rank-num { font-size: 0.7rem; color: #64748b; }
        .news-rank-score { font-size: 1.125rem; font-weight: 700; background: linear-gradient(135deg, #818cf8, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .news-content { flex: 1; min-width: 0; }
        .news-meta { display: flex; flex-wrap: wrap; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem; }
        .news-badge { font-size: 0.7rem; font-weight: 600; padding: 0.25rem 0.75rem; border-radius: 8px; border: 1px solid; }
        .news-badge.cap { background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(168, 85, 247, 0.2)); color: #c4b5fd; border-color: rgba(139, 92, 246, 0.3); }
        .news-badge.eco { background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(20, 184, 166, 0.2)); color: #6ee7b7; border-color: rgba(16, 185, 129, 0.3); }
        .news-badge.irr { background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(249, 115, 22, 0.2)); color: #fcd34d; border-color: rgba(245, 158, 11, 0.3); }
        .news-badge.tml { background: linear-gradient(135deg, rgba(6, 182, 212, 0.2), rgba(59, 130, 246, 0.2)); color: #67e8f9; border-color: rgba(6, 182, 212, 0.3); }
        .news-badge.sys { background: linear-gradient(135deg, rgba(244, 63, 94, 0.2), rgba(236, 72, 153, 0.2)); color: #fda4af; border-color: rgba(244, 63, 94, 0.3); }
        .news-source { font-size: 0.75rem; color: #94a3b8; font-weight: 500; }
        .news-date { font-size: 0.75rem; color: #64748b; }
        .news-dot { color: #475569; }
        .news-title { font-size: 1.1rem; font-weight: 600; color: white; margin-bottom: 0.75rem; line-height: 1.4; }
        .news-card:hover .news-title { color: #c7d2fe; }
        .news-summary { font-size: 0.875rem; color: #94a3b8; margin-bottom: 1rem; line-height: 1.6; }
        .score-bars { display: grid; grid-template-columns: repeat(5, 1fr); gap: 0.5rem; padding: 0.75rem; background: rgba(0, 0, 0, 0.3); border-radius: 12px; margin-bottom: 1rem; }
        .score-bar-item { text-align: center; }
        .score-bar-label { font-size: 0.6rem; color: #475569; margin-bottom: 0.25rem; }
        .score-bar-track { height: 4px; background: #1e293b; border-radius: 2px; overflow: hidden; }
        .score-bar-fill { height: 100%; }
        .score-bar-fill.cap { background: #8b5cf6; }
        .score-bar-fill.eco { background: #10b981; }
        .score-bar-fill.irr { background: #f59e0b; }
        .score-bar-fill.tml { background: #06b6d4; }
        .score-bar-fill.sys { background: #f43f5e; }
        .score-bar-value { font-size: 0.7rem; font-weight: 500; margin-top: 0.25rem; }
        .score-bar-value.high { color: #34d399; }
        .score-bar-value.mid { color: #fbbf24; }
        .score-bar-value.low { color: #64748b; }
        .news-link { display: inline-flex; align-items: center; gap: 0.5rem; color: #818cf8; font-size: 0.875rem; font-weight: 500; text-decoration: none; transition: color 0.2s; }
        .news-link:hover { color: #a5b4fc; }
        .news-link svg { width: 16px; height: 16px; }
        .pagination { display: flex; align-items: center; justify-content: center; gap: 1rem; margin-top: 2.5rem; padding-top: 2rem; border-top: 1px solid rgba(255, 255, 255, 0.05); }
        .pagination-btn { display: flex; align-items: center; gap: 0.5rem; padding: 0.625rem 1.25rem; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; color: #cbd5e1; font-size: 0.875rem; font-weight: 500; cursor: pointer; transition: all 0.2s; }
        .pagination-btn:hover:not(:disabled) { background: rgba(255, 255, 255, 0.1); }
        .pagination-btn:disabled { opacity: 0.3; cursor: not-allowed; }
        .pagination-btn svg { width: 16px; height: 16px; }
        .pagination-info { padding: 0.5rem 1rem; background: rgba(255, 255, 255, 0.05); border-radius: 12px; font-size: 0.875rem; color: #64748b; }
        .pagination-info span { color: white; font-weight: 600; }
        footer { border-top: 1px solid rgba(255, 255, 255, 0.05); margin-top: 2rem; background: rgba(0, 0, 0, 0.3); }
        .footer-inner { max-width: 900px; margin: 0 auto; padding: 1.25rem 1.5rem; display: flex; flex-wrap: wrap; justify-content: space-between; gap: 0.75rem; font-size: 0.75rem; color: #475569; }
        .hidden { display: none !important; }
        @media (max-width: 640px) {
            .news-inner { flex-direction: column; gap: 1rem; }
            .news-rank { width: 100%; height: auto; flex-direction: row; padding: 0.75rem; gap: 0.5rem; }
            .scoring-items { gap: 0.75rem; }
            .pagination { flex-direction: column; }
        }
    </style>
</head>
<body>
    <div class="bg-glow"></div>
    <div class="grid-overlay"></div>
    
    <div class="container">
        <header>
            <div class="header-inner">
                <div class="logo-section">
                    <div class="logo-icon">
                        <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
                        </svg>
                    </div>
                    <div class="logo-text">
                        <h1>Organizational AI <span>Radar</span></h1>
                        <p>News Ranked by Importance • Updated: %%UPDATE_DATE%%</p>
                    </div>
                </div>
            </div>
        </header>

        <div class="scoring-legend">
            <div class="scoring-box">
                <div class="scoring-title">Importance Scoring</div>
                <div class="scoring-items">
                    <div class="scoring-item">
                        <div class="scoring-dot cap"></div>
                        <span class="scoring-label cap">Capability</span>
                        <span class="scoring-weight">30%</span>
                        <div class="tooltip">
                            <div class="tooltip-title">Capability Inflection (30%)</div>
                            <div class="tooltip-question">Does this development materially change what AI systems can do?</div>
                        </div>
                    </div>
                    <div class="scoring-item">
                        <div class="scoring-dot eco"></div>
                        <span class="scoring-label eco">Economic</span>
                        <span class="scoring-weight">25%</span>
                        <div class="tooltip">
                            <div class="tooltip-title">Economic Surface Area (25%)</div>
                            <div class="tooltip-question">How much of the economy does this news touch or threaten to reshape?</div>
                        </div>
                    </div>
                    <div class="scoring-item">
                        <div class="scoring-dot irr"></div>
                        <span class="scoring-label irr">Irreversibility</span>
                        <span class="scoring-weight">20%</span>
                        <div class="tooltip">
                            <div class="tooltip-title">Irreversibility (20%)</div>
                            <div class="tooltip-question">Does this event lock the AI trajectory into a new path?</div>
                        </div>
                    </div>
                    <div class="scoring-item">
                        <div class="scoring-dot tml"></div>
                        <span class="scoring-label tml">Timeline</span>
                        <span class="scoring-weight">15%</span>
                        <div class="tooltip">
                            <div class="tooltip-title">Timeline Effect (15%)</div>
                            <div class="tooltip-question">Does this news meaningfully speed up or slow down AI progress overall?</div>
                        </div>
                    </div>
                    <div class="scoring-item">
                        <div class="scoring-dot sys"></div>
                        <span class="scoring-label sys">Systemic</span>
                        <span class="scoring-weight">10%</span>
                        <div class="tooltip">
                            <div class="tooltip-title">Systemic Effects (10%)</div>
                            <div class="tooltip-question">Does this news trigger cascading effects beyond AI itself?</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <main>
            <div id="newsContainer" class="news-list"></div>
            <div id="paginationContainer" class="pagination">
                <button class="pagination-btn" id="prevBtn" onclick="prevPage()">
                    <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" /></svg>
                    Previous
                </button>
                <div class="pagination-info"><span id="pageInfo">1-5</span> / <span id="totalCount">0</span></div>
                <button class="pagination-btn" id="nextBtn" onclick="nextPage()">
                    Next
                    <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" /></svg>
                </button>
            </div>
        </main>

        <footer>
            <div class="footer-inner">
                <span>Organizational AI Radar • Auto-updated daily at 7:00 AM CET</span>
                <span>Powered by Claude AI</span>
            </div>
        </footer>
    </div>

    <script>
        const newsData = %%NEWS_DATA%%;

        let currentPage = 0;
        const itemsPerPage = 5;

        function renderNews() {
            const container = document.getElementById('newsContainer');
            const start = currentPage * itemsPerPage;
            const end = Math.min(start + itemsPerPage, newsData.length);
            const currentNews = newsData.slice(start, end);

            const badgeLabels = {
                capability: { label: 'Capability', icon: '⬡', class: 'cap' },
                economic: { label: 'Economic', icon: '◈', class: 'eco' },
                irreversibility: { label: 'Irreversible', icon: '◆', class: 'irr' },
                timeline: { label: 'Timeline', icon: '▲', class: 'tml' },
                systemic: { label: 'Systemic', icon: '●', class: 'sys' }
            };

            container.innerHTML = currentNews.map((item, index) => {
                const badge = badgeLabels[item.primaryDriver] || badgeLabels.capability;
                const globalIndex = start + index + 1;
                const scores = item.scores;
                const getScoreClass = (score) => score >= 7 ? 'high' : score >= 4 ? 'mid' : 'low';

                return `
                    <article class="news-card">
                        <div class="news-inner">
                            <div class="news-rank">
                                <span class="news-rank-num">#${globalIndex}</span>
                                <span class="news-rank-score">${item.weightedScore.toFixed(1)}</span>
                            </div>
                            <div class="news-content">
                                <div class="news-meta">
                                    <span class="news-badge ${badge.class}">${badge.icon} ${badge.label}</span>
                                    <span class="news-source">${item.source}</span>
                                    <span class="news-dot">•</span>
                                    <span class="news-date">${item.date}</span>
                                </div>
                                <h2 class="news-title">${item.title}</h2>
                                <p class="news-summary">${item.summary}</p>
                                <div class="score-bars">
                                    <div class="score-bar-item">
                                        <div class="score-bar-label">CAP</div>
                                        <div class="score-bar-track"><div class="score-bar-fill cap" style="width: ${scores.capability * 10}%"></div></div>
                                        <div class="score-bar-value ${getScoreClass(scores.capability)}">${scores.capability}</div>
                                    </div>
                                    <div class="score-bar-item">
                                        <div class="score-bar-label">ECO</div>
                                        <div class="score-bar-track"><div class="score-bar-fill eco" style="width: ${scores.economic * 10}%"></div></div>
                                        <div class="score-bar-value ${getScoreClass(scores.economic)}">${scores.economic}</div>
                                    </div>
                                    <div class="score-bar-item">
                                        <div class="score-bar-label">IRR</div>
                                        <div class="score-bar-track"><div class="score-bar-fill irr" style="width: ${scores.irreversibility * 10}%"></div></div>
                                        <div class="score-bar-value ${getScoreClass(scores.irreversibility)}">${scores.irreversibility}</div>
                                    </div>
                                    <div class="score-bar-item">
                                        <div class="score-bar-label">TML</div>
                                        <div class="score-bar-track"><div class="score-bar-fill tml" style="width: ${scores.timeline * 10}%"></div></div>
                                        <div class="score-bar-value ${getScoreClass(scores.timeline)}">${scores.timeline}</div>
                                    </div>
                                    <div class="score-bar-item">
                                        <div class="score-bar-label">SYS</div>
                                        <div class="score-bar-track"><div class="score-bar-fill sys" style="width: ${scores.systemic * 10}%"></div></div>
                                        <div class="score-bar-value ${getScoreClass(scores.systemic)}">${scores.systemic}</div>
                                    </div>
                                </div>
                                <a href="${item.url}" target="_blank" rel="noopener noreferrer" class="news-link">
                                    Read full article
                                    <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                                        <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 19.5l15-15m0 0H8.25m11.25 0v11.25" />
                                    </svg>
                                </a>
                            </div>
                        </div>
                    </article>
                `;
            }).join('');

            updatePagination();
        }

        function updatePagination() {
            const start = currentPage * itemsPerPage + 1;
            const end = Math.min((currentPage + 1) * itemsPerPage, newsData.length);
            document.getElementById('pageInfo').textContent = start + '-' + end;
            document.getElementById('totalCount').textContent = newsData.length;
            document.getElementById('prevBtn').disabled = currentPage === 0;
            document.getElementById('nextBtn').disabled = end >= newsData.length;
        }

        function prevPage() {
            if (currentPage > 0) { currentPage--; renderNews(); window.scrollTo({ top: 0, behavior: 'smooth' }); }
        }

        function nextPage() {
            if ((currentPage + 1) * itemsPerPage < newsData.length) { currentPage++; renderNews(); window.scrollTo({ top: 0, behavior: 'smooth' }); }
        }

        renderNews();
    </script>
</body>
</html>'''


def fetch_news_from_claude():
    """Fetch and score AI news using Claude API with web search."""
    client = anthropic.Anthropic()
    
    prompt = """Search for the latest AI and artificial intelligence news from the past 2-3 days. 
Focus on respected sources: MIT Technology Review, TechCrunch, Reuters, Wired, Ars Technica, The Verge, Nature, Science, Financial Times, Bloomberg, CNBC.

Score and rank each news item using these 5 criteria with exact weightings:

1. CAPABILITY INFLECTION (30% weight)
   Question: Does this development materially change what AI systems can do?
   Score 0-10: 0=no capability change, 10=fundamental new capability unlocked

2. ECONOMIC SURFACE AREA (25% weight)
   Question: How much of the economy does this news touch or threaten to reshape?
   Score 0-10: 0=niche impact, 10=economy-wide disruption

3. IRREVERSIBILITY (20% weight)
   Question: Does this event lock the AI trajectory into a new path?
   Score 0-10: 0=easily reversed, 10=permanent trajectory shift

4. TIMELINE EFFECT (15% weight)
   Question: Does this news meaningfully speed up or slow down AI progress overall?
   Score 0-10: 0=no timeline impact, 10=major acceleration or deceleration

5. SYSTEMIC EFFECTS (10% weight)
   Question: Does this news trigger cascading effects beyond AI itself?
   Score 0-10: 0=contained to AI, 10=ripples across society/geopolitics

Calculate weighted score: (capability×0.30) + (economic×0.25) + (irreversibility×0.20) + (timeline×0.15) + (systemic×0.10)

Return ONLY a JSON array with 15 news items, SORTED BY WEIGHTED SCORE (highest first).

Each item must have:
- source: publication name
- date: publication date (e.g., "Jan 5, 2026")
- title: article headline
- summary: 2-3 sentence summary of key points
- url: full article URL
- scores: { "capability": 0-10, "economic": 0-10, "irreversibility": 0-10, "timeline": 0-10, "systemic": 0-10 }
- weightedScore: calculated total (0-10 scale, one decimal)
- primaryDriver: "capability" | "economic" | "irreversibility" | "timeline" | "systemic" (whichever scored highest)

Return ONLY valid JSON array. No markdown, no backticks, no explanation."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search"
        }],
        messages=[{"role": "user", "content": prompt}]
    )
    
    # Extract text from response
    json_text = ""
    for block in response.content:
        if hasattr(block, 'text'):
            json_text += block.text
    
    # Clean and parse JSON
    json_text = re.sub(r'```json|```', '', json_text).strip()
    
    # Find JSON array in response
    match = re.search(r'\[[\s\S]*\]', json_text)
    if match:
        news_data = json.loads(match.group())
        return news_data
    else:
        raise ValueError("Could not parse news JSON from response")


def generate_html(news_data):
    """Generate HTML with embedded news data."""
    update_date = datetime.now().strftime("%B %d, %Y at %H:%M UTC")
    
    html = HTML_TEMPLATE.replace('%%NEWS_DATA%%', json.dumps(news_data, indent=2))
    html = html.replace('%%UPDATE_DATE%%', update_date)
    
    return html


def main():
    print("Fetching latest AI news...")
    news_data = fetch_news_from_claude()
    print(f"Fetched {len(news_data)} news items")
    
    # Sort by weightedScore in descending order (highest first)
    news_data.sort(key=lambda x: float(x.get('weightedScore', 0)), reverse=True)
    print("Sorted news by importance score (descending)")
    
    print("Generating HTML...")
    html = generate_html(news_data)
    
    print("Writing index.html...")
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    print("Done!")


if __name__ == "__main__":
    main()
