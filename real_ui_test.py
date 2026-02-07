# =====================================
# FULL NEURONEXAI QA ENGINE V3 — STREAMLIT FIXED
# =====================================

import streamlit as st
import time, os, requests, statistics
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# =====================================
# PAGE CONFIG
# =====================================
st.set_page_config(page_title="AI QA Platform", layout="wide")

# =====================================
# SMART PAGE SCROLLER
# =====================================
def auto_scroll(driver):
    last = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1.2)
        new = driver.execute_script("return document.body.scrollHeight")
        if new == last:
            break
        last = new

# =====================================
# AI SCORING ENGINE
# =====================================
def ai_score_engine(metrics):
    score = 100

    if metrics["load_time"] > 6: score -= 15
    if metrics["broken_links"] > 5: score -= 20
    if metrics["broken_images"] > 5: score -= 15
    if metrics["clickable_buttons"] < 5: score -= 10
    if metrics["functional_inputs"] == 0: score -= 10
    if not metrics["https"]: score -= 15
    if metrics["avg_response"] > 2.5: score -= 10

    score = max(0, min(score, 100))

    grade = "HIGH RISK"
    if score > 85: grade = "EXCELLENT"
    elif score > 65: grade = "GOOD"
    elif score > 45: grade = "AVERAGE"

    future_risk = "LOW"
    if score < 60: future_risk = "MEDIUM"
    if score < 40: future_risk = "HIGH"

    return score, grade, future_risk

# =====================================
# GLOBAL AI QA ENGINE
# =====================================
def run_global_ai_qa(url):
    report = []
    screenshot = "site_preview.png"

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    metrics = {
        "broken_links": 0,
        "broken_images": 0,
        "clickable_buttons": 0,
        "functional_inputs": 0,
        "avg_response": 0,
        "load_time": 0,
        "https": url.startswith("https")
    }

    broken_links = []
    working_links = []
    broken_images = []
    working_images = []

    try:
        start = time.time()
        driver.get(url)
        time.sleep(4)
        auto_scroll(driver)

        metrics["load_time"] = round(time.time() - start, 2)
        title = driver.title

        buttons = driver.find_elements(By.TAG_NAME, "button")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        links = driver.find_elements(By.TAG_NAME, "a")
        images = driver.find_elements(By.TAG_NAME, "img")
        forms = driver.find_elements(By.TAG_NAME, "form")

        for btn in buttons[:40]:
            try:
                driver.execute_script("arguments[0].scrollIntoView();", btn)
                btn.click()
                metrics["clickable_buttons"] += 1
                time.sleep(0.1)
            except:
                pass

        for inp in inputs[:40]:
            try:
                inp.send_keys("AI QA Test")
                metrics["functional_inputs"] += 1
            except:
                pass

        response_times = []
        for link in links[:100]:
            try:
                href = link.get_attribute("href")
                if href and href.startswith("http"):
                    start = time.time()
                    r = requests.head(href, timeout=5)
                    response_times.append(time.time() - start)

                    if r.status_code >= 400:
                        metrics["broken_links"] += 1
                        broken_links.append(href)
                    else:
                        working_links.append(href)
            except:
                metrics["broken_links"] += 1

        metrics["avg_response"] = round(statistics.mean(response_times), 2) if response_times else 0

        for img in images[:80]:
            try:
                src = img.get_attribute("src")
                if src:
                    r = requests.get(src, timeout=5)
                    if r.status_code >= 400:
                        metrics["broken_images"] += 1
                        broken_images.append(src)
                    else:
                        working_images.append(src)
            except:
                metrics["broken_images"] += 1

        api_calls = 0
        try:
            perf = driver.execute_script("return window.performance.getEntriesByType('resource')")
            api_calls = len([x for x in perf if x["initiatorType"] in ["fetch","xmlhttprequest"]])
        except:
            pass

        driver.save_screenshot(screenshot)

        score, grade, risk = ai_score_engine(metrics)

        link_health = 100 if len(links)==0 else round((len(links)-metrics["broken_links"]) / len(links) * 100, 2)
        image_health = 100 if len(images)==0 else round((len(images)-metrics["broken_images"]) / len(images) * 100, 2)

        report += [
            f"URL: {url}",
            f"Page Title: {title}",
            f"Load Time: {metrics['load_time']} sec",
            f"Buttons Found: {len(buttons)}",
            f"Clickable Buttons: {metrics['clickable_buttons']}",
            f"Inputs Found: {len(inputs)}",
            f"Functional Inputs: {metrics['functional_inputs']}",
            f"Links Found: {len(links)}",
            f"Broken Links: {metrics['broken_links']}",
            f"Link Health Score: {link_health}%",
            f"Images Found: {len(images)}",
            f"Broken Images: {metrics['broken_images']}",
            f"Image Health Score: {image_health}%",
            f"Forms Found: {len(forms)}",
            f"Backend API Calls: {api_calls}",
            f"HTTPS Enabled: {metrics['https']}",
            f"Average Backend Response: {metrics['avg_response']} sec",
            "",
            f"FINAL SCORE: {score}/100",
            f"QUALITY GRADE: {grade}",
            f"AI FUTURE FAILURE RISK: {risk}",
            "",
            "AI RECOMMENDATIONS:"
        ]

        if metrics["broken_links"] > 0: report.append("- Fix broken links")
        if metrics["broken_images"] > 0: report.append("- Repair broken images")
        if metrics["clickable_buttons"] < 5: report.append("- Improve button reliability")
        if metrics["functional_inputs"] == 0: report.append("- Fix form input validation")
        if metrics["load_time"] > 6: report.append("- Improve performance & caching")
        if not metrics["https"]: report.append("- Enable HTTPS security")

        report.append("\nBROKEN LINKS:")
        report += broken_links if broken_links else ["None"]

        report.append("\nBROKEN IMAGES:")
        report += broken_images if broken_images else ["None"]

    except Exception as e:
        report.append(f"CRITICAL ERROR: {str(e)}")

    finally:
        driver.quit()

    file_path = "global_ai_qa_report.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report))

    return report, file_path, screenshot

# =====================================
# PREMIUM STREAMLIT UI DESIGN
# =====================================

st.markdown("""
<style>

body {
    background: radial-gradient(circle at top, #020617, #000000);
    color: white;
}

/* Moving AI Grid */
.ai-grid {
    position: fixed;
    inset: 0;
    z-index: -1;
    background: repeating-linear-gradient(
        0deg,
        rgba(56,189,248,0.07) 0px,
        rgba(56,189,248,0.03) 2px,
        transparent 6px
    );
    animation: gridMove 10s linear infinite;
}

@keyframes gridMove {
    from { background-position: 0 0; }
    to { background-position: 0 400px; }
}

/* Title Glow */
.main-title {
    font-size: 44px;
    font-weight: bold;
    color: #38bdf8;
    text-align: center;
    text-shadow: 0 0 20px #22d3ee;
    animation: glow 2s infinite alternate;
}

@keyframes glow {
    from { text-shadow: 0 0 12px #38bdf8; }
    to { text-shadow: 0 0 28px #22d3ee; }
}

/* Glass Panel */
.glass-panel {
    background: rgba(10,15,30,0.92);
    border-radius: 22px;
    padding: 28px;
    border: 1px solid rgba(56,189,248,0.4);
    box-shadow: 0 0 35px rgba(56,189,248,0.3);
}

/* Button */
.stButton > button {
    background: linear-gradient(135deg, #38bdf8, #22d3ee);
    color: black;
    border-radius: 14px;
    font-weight: bold;
    padding: 14px 24px;
    transition: 0.25s ease;
}

.stButton > button:hover {
    transform: scale(1.05);
}

/* Footer Locked */
.footer {
    margin-top: 60px;
    padding: 25px;
    text-align: center;
    font-size: 14px;
    color: #94a3b8;
    border-top: 1px solid #38bdf8;
    background: rgba(5,10,25,0.95);
}

.footer span {
    color: #22d3ee;
    font-weight: bold;
}

</style>

<div class="ai-grid"></div>
""", unsafe_allow_html=True)

# =====================================
# UI CONTENT
# =====================================

st.markdown("<div class='main-title'>AI for QA - Global Website Intelligence Engine</div>", unsafe_allow_html=True)

st.markdown("""
<div class="glass-panel">
AI-Powered Website Testing for UI • Backend • Performance • Security • Stability  
Built for Developers, Startups & Enterprises Worldwide  
</div>
""", unsafe_allow_html=True)

st.info("Created by **Sahil Khan - AI Engineer**")

url = st.text_input("Enter Website URL")

if st.button("Run Global AI QA Test"):
    if url:
        with st.spinner("AI is testing website deeply...I appreciate your patience. This will not take longer than 2 minutes"):
            report, report_file, screenshot = run_global_ai_qa(url)

        st.success("Test Completed Successfully")

        st.markdown("<div class='glass-panel'>" + "<br>".join(report) + "</div>", unsafe_allow_html=True)

        if os.path.exists(screenshot):
            st.image(screenshot, caption="Website Screenshot")

        with open(report_file, "rb") as f:
            st.download_button("Download AI QA Report", f, file_name="global_ai_qa_report.txt")

# =====================================
# PERMANENT FOOTER — YOUR BRAND
# =====================================

st.markdown("""
<div class="footer">
<span>Sahil Khan - AI Engineer</span><br>
AI Engineer for Health Sciences • AI Engineer for Software Development • AI Engineer for Human Brain & Neurosciences<br>
Currently pursuing a Bachelor's in Artificial Intelligence with hands-on experience from some of the world's largest companies. Experienced in teaching AI, conducting research, and developing advanced AI solutions.<br>
Creator of the Global AI QA Engine for testing websites worldwide.<br>
Focused on Artificial Intelligence, Machine Learning, Robotics, Computer Vision, and Deep Learning.<br>
This platform ensures world-class website quality, performance, and security.
""", unsafe_allow_html=True)
