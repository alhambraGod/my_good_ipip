"""AI-powered personality report generation using OpenAI GPT-4o."""

from openai import OpenAI

from config import settings

SYSTEM_PROMPT = """You are an expert psychometrician and career counselor with deep expertise in the Big Five personality model (IPIP-NEO) and the Indian professional landscape. You create insightful, personalized personality assessment reports.

Your reports must be:
- Evidence-based and grounded in the Big Five personality science
- Culturally relevant to the Indian context (career paths, social dynamics, workplace culture)
- Encouraging and growth-oriented — never judgmental
- Actionable with specific career and development recommendations
- Written in clear, professional English accessible to Indian professionals and students

IMPORTANT GUIDELINES:
- Reference Indian career paths: IT/software engineering, data science, government services (UPSC/SSC), startups, consulting, finance, healthcare, education, legal
- Consider Indian workplace dynamics: hierarchical structures, team orientation, respect for seniority
- Include both multinational and Indian company cultures
- Reference relevant skills: communication, leadership, technical aptitude, adaptability
- Be specific — avoid generic advice that could apply to anyone"""

REPORT_PROMPT_TEMPLATE = """Generate a comprehensive, personalized personality assessment report based on the following Big Five personality scores (0-100 scale) and percentile rankings.

## Scores
- Openness to Experience: {openness}/100 (Percentile: {openness_pct}th)
- Conscientiousness: {conscientiousness}/100 (Percentile: {conscientiousness_pct}th)
- Extraversion: {extraversion}/100 (Percentile: {extraversion_pct}th)
- Agreeableness: {agreeableness}/100 (Percentile: {agreeableness_pct}th)
- Emotional Stability: {emotional_stability}/100 (Percentile: {emotional_stability_pct}th)

Note: Emotional Stability = 100 - Neuroticism score. Higher = more stable.

## Report Structure (use these exact headings in markdown):

### Executive Summary
A compelling 3-4 sentence overview of this person's unique personality profile. Highlight their most distinctive traits and what makes their combination special.

### Your Personality Profile

For EACH of the 5 dimensions, write a detailed paragraph covering:
- What their score means in practical terms
- How this trait likely manifests in daily life and work
- Specific strengths this trait brings
- Potential challenges to be aware of

Use these subheadings:
#### Openness to Experience — [Score]/100
#### Conscientiousness — [Score]/100
#### Extraversion — [Score]/100
#### Agreeableness — [Score]/100
#### Emotional Stability — [Score]/100

### Career Recommendations
Based on their unique trait combination, recommend 5-7 specific career paths that would be an excellent fit. For each:
- Name the career/role
- Explain WHY their personality traits make this a great match
- Include a mix of corporate, startup, and independent paths
- Reference Indian market opportunities where relevant

### Your Strengths
List and explain 5 key personality-driven strengths with concrete examples of how they show up.

### Growth Opportunities
Identify 3-4 areas for personal development. Frame these positively — as opportunities, not weaknesses. Include specific, actionable strategies.

### Relationship & Team Dynamics
How their personality affects:
- Working with teams and managers
- Communication style preferences
- Conflict resolution approach
- Leadership potential and style

### Actionable Next Steps
Provide 5 concrete, specific actions they can take this week to leverage their personality strengths for career and personal growth.

Write the full report in markdown format. Be specific, insightful, and avoid generic statements. This person paid for this report — make it worth every rupee."""


async def generate_report(scores: dict[str, float], percentiles: dict[str, int]) -> str:
    """Generate a personalized AI report using OpenAI GPT-4o."""

    # Convert neuroticism to emotional stability for more positive framing
    emotional_stability = round(100 - scores.get("neuroticism", 50), 1)
    emotional_stability_pct = 100 - percentiles.get("neuroticism", 50)

    prompt = REPORT_PROMPT_TEMPLATE.format(
        openness=scores.get("openness", 50),
        openness_pct=percentiles.get("openness", 50),
        conscientiousness=scores.get("conscientiousness", 50),
        conscientiousness_pct=percentiles.get("conscientiousness", 50),
        extraversion=scores.get("extraversion", 50),
        extraversion_pct=percentiles.get("extraversion", 50),
        agreeableness=scores.get("agreeableness", 50),
        agreeableness_pct=percentiles.get("agreeableness", 50),
        emotional_stability=emotional_stability,
        emotional_stability_pct=emotional_stability_pct,
    )

    if not settings.OPENAI_API_KEY:
        return _generate_fallback_report(scores, percentiles)

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=4000,
    )
    return response.choices[0].message.content


def _generate_fallback_report(scores: dict[str, float], percentiles: dict[str, int]) -> str:
    """Generate a template-based report when OpenAI API is unavailable."""

    emotional_stability = round(100 - scores.get("neuroticism", 50), 1)

    def level(score):
        if score >= 70:
            return "high"
        elif score >= 40:
            return "moderate"
        return "low"

    o, c, e, a = scores.get("openness", 50), scores.get("conscientiousness", 50), scores.get("extraversion", 50), scores.get("agreeableness", 50)
    es = emotional_stability

    return f"""### Executive Summary

Your personality profile reveals a unique combination of traits that shape how you approach work, relationships, and personal growth. With **{level(o)} openness** ({o}/100), **{level(c)} conscientiousness** ({c}/100), **{level(e)} extraversion** ({e}/100), **{level(a)} agreeableness** ({a}/100), and **{level(es)} emotional stability** ({es}/100), you bring a distinctive perspective to everything you do.

### Your Personality Profile

#### Openness to Experience — {o}/100
Your openness score of {o} places you in the **{percentiles.get("openness", 50)}th percentile**. {"You are highly curious and imaginative, drawn to new ideas, technologies, and creative problem-solving. You thrive in environments that encourage innovation and intellectual exploration." if o >= 60 else "You tend to prefer practical, tried-and-tested approaches. You value stability and reliability, which makes you an excellent executor of established processes and systems."}

#### Conscientiousness — {c}/100
With a conscientiousness score of {c} ({percentiles.get("conscientiousness", 50)}th percentile), {"you are disciplined, organized, and goal-oriented. You excel at planning ahead, meeting deadlines, and delivering high-quality work consistently. These traits are highly valued in structured environments like IT services, finance, and government sectors." if c >= 60 else "you take a flexible approach to structure and planning. While this gives you adaptability, you may benefit from developing stronger organizational systems to support your ambitions."}

#### Extraversion — {e}/100
Your extraversion score of {e} ({percentiles.get("extraversion", 50)}th percentile) indicates that {"you are energized by social interactions and enjoy collaborative environments. You likely excel in roles that involve networking, team leadership, and client engagement." if e >= 60 else "you prefer meaningful one-on-one interactions over large group settings. You bring depth and thoughtfulness to your relationships and work best in focused, less stimulating environments."}

#### Agreeableness — {a}/100
At {a}/100 ({percentiles.get("agreeableness", 50)}th percentile), {"you are naturally empathetic and cooperative. You prioritize harmony in relationships and are skilled at building trust and consensus within teams." if a >= 60 else "you maintain a healthy balance between cooperation and assertiveness. You can advocate for your own needs while still being a team player, which is valuable in competitive professional environments."}

#### Emotional Stability — {es}/100
Your emotional stability score of {es} ({100 - percentiles.get("neuroticism", 50)}th percentile) suggests that {"you handle stress and pressure with composure. This resilience is a significant asset in high-stakes environments like startups, consulting, and leadership roles." if es >= 60 else "you experience emotions deeply and may be more sensitive to stress. This emotional awareness can be channeled into empathy, creativity, and passion for your work."}

### Career Recommendations

Based on your unique personality profile, these career paths align well with your traits:

1. **Software Engineering / Data Science** — Your combination of {"curiosity and" if o >= 60 else ""} analytical thinking makes technical roles a strong fit
2. **Product Management** — Balancing stakeholder needs with strategic vision leverages your interpersonal and planning skills
3. **Consulting** — {"Your social energy and" if e >= 60 else "Your analytical depth and"} problem-solving abilities are ideal for advisory roles
4. **Entrepreneurship / Startups** — India's growing startup ecosystem offers opportunities that match your {"innovative" if o >= 60 else "practical"} mindset
5. **Education / Training** — Sharing knowledge and developing others aligns with your {"collaborative" if a >= 60 else "structured"} approach
6. **Government Services (UPSC/State Services)** — {"Your disciplined nature suits" if c >= 60 else "With focused preparation, you could excel in"} India's prestigious civil services

### Your Strengths

1. **{"Innovation & Curiosity" if o >= 60 else "Practical Problem-Solving"}** — You {"naturally generate creative solutions" if o >= 60 else "find reliable, efficient solutions to challenges"}
2. **{"Discipline & Reliability" if c >= 60 else "Flexibility & Adaptability"}** — {"Others can count on you to deliver" if c >= 60 else "You adapt quickly to changing circumstances"}
3. **{"Social Intelligence" if e >= 60 else "Deep Focus"}** — {"You read rooms well and build connections easily" if e >= 60 else "You concentrate deeply and produce thoughtful work"}
4. **{"Empathy & Teamwork" if a >= 60 else "Balanced Assertiveness"}** — {"You create harmonious team environments" if a >= 60 else "You stand your ground while respecting others"}
5. **{"Emotional Resilience" if es >= 60 else "Emotional Awareness"}** — {"You stay composed under pressure" if es >= 60 else "Your sensitivity helps you understand others deeply"}

### Growth Opportunities

1. **{"Challenge Your Comfort Zone" if o < 60 else "Focus Your Creativity"}** — {"Try one new approach or tool each week to expand your repertoire" if o < 60 else "Channel your many ideas into focused execution with clear priorities"}
2. **{"Build Structured Habits" if c < 60 else "Embrace Flexibility"}** — {"Start with a simple daily planning routine to boost productivity" if c < 60 else "Practice going with the flow when plans change — not everything needs a system"}
3. **{"Develop Your Network" if e < 60 else "Cultivate Depth"}** — {"Attend one professional event per month to gradually expand your comfort zone" if e < 60 else "Invest in deeper one-on-one relationships alongside your wide network"}
4. **{"Practice Stress Management" if es < 60 else "Stay Connected to Emotions"}** — {"Explore mindfulness, yoga, or journaling to build emotional resilience" if es < 60 else "Ensure your composure doesn't distance you from your own feelings or others' concerns"}

### Relationship & Team Dynamics

In team settings, you tend to be {"a collaborative and energetic contributor" if e >= 60 else "a thoughtful and focused contributor"} who {"prioritizes group harmony" if a >= 60 else "balances team needs with personal standards"}. Your communication style is {"direct and engaging" if e >= 60 else "considered and precise"}, and you handle conflict by {"seeking compromise and understanding" if a >= 60 else "addressing issues logically and fairly"}.

{"As a leader, your composure and reliability inspire confidence in your team." if es >= 60 and c >= 60 else "As you grow into leadership roles, developing consistent habits and stress management techniques will strengthen your impact."}

### Actionable Next Steps

1. **This week**: Identify your top career interest from the recommendations above and research 3 professionals in that field on LinkedIn
2. **This week**: Start a brief daily reflection practice — 5 minutes journaling about what went well and what you learned
3. **This week**: Have one conversation with a mentor, colleague, or friend about your career aspirations
4. **This week**: Take note of situations where your personality strengths helped you succeed — building self-awareness is powerful
5. **This week**: Set one small, specific goal that stretches you slightly outside your comfort zone"""
