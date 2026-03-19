import streamlit as st
import anthropic
import base64
import json
import plotly.graph_objects as go
import pandas as pd
import os

# 1. Setup
st.set_page_config(page_title="Insight Architect 2026", layout="wide")
st.title("📊 Insight Architect")

# 2. Key Handling (Works for Streamlit Secrets or Environment Variables)
if "ANTHROPIC_API_KEY" in st.secrets:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
elif os.environ.get("ANTHROPIC_API_KEY"):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
else:
    api_key = st.sidebar.text_input("Enter Anthropic API Key", type="password")

client = anthropic.Anthropic(api_key=api_key) if api_key else None

# 3. AI Logic
def process_charts(files):
    images = []
    for f in files:
        b64 = base64.b64encode(f.read()).decode("utf-8")
        images.append({
            "type": "image", 
            "source": {"type": "base64", "media_type": "image/png", "data": b64}
        })
    
    prompt = """
    Analyze these charts. 1. Extract raw data. 2. Normalize X-axis categories.
    3. Write a 3-sentence 'summary' of trends. 4. Provide 3 forecast points.
    Return ONLY JSON: 
    { "summary": "...", "categories": [], "datasets": {}, "forecast": {}, "forecast_categories": [] }
    """
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=3000,
        messages=[{"role": "user", "content": [*images, {"type": "text", "text": prompt}]}]
    )
    return json.loads(response.content[0].text)

# 4. UI
uploaded_files = st.file_uploader("Upload Chart Screenshots", accept_multiple_files=True)

if uploaded_files and client:
    if st.button("🚀 Analyze & Compare"):
        try:
            res = process_charts(uploaded_files)
            st.info(res['summary'])
            
            fig = go.Figure()
            for name, vals in res['datasets'].items():
                fig.add_trace(go.Scatter(name=name, x=res['categories'], y=vals, mode='lines+markers'))
                if 'forecast' in res:
                    fig.add_trace(go.Scatter(name=f"{name} (Forecast)", 
                                           x=res['forecast_categories'], 
                                           y=res['forecast'][name], 
                                           line=dict(dash='dash')))
            
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(pd.DataFrame(res['datasets'], index=res['categories']))
        except Exception as e:
            st.error(f"Error: {e}")
