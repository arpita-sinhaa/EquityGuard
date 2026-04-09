import os
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY", "mock-key"))

def generate_citizen_explanation(domain: str, disparity_ratio: float, sample_size: int) -> str:
    if os.getenv("GEMINI_API_KEY") is None:
        return "Simulated Gemini Response: This statistical indication of bias reveals that historical approval rates for this group are substantially lower than the reference group. The disparity suggests systemic hurdles in this domain."
        
    prompt = f"""
You are an expert in explaining statistical fairness metrics in plain language.
A citizen bias check for the domain '{domain}' returned a statistical indication of bias.
The disparity ratio is {disparity_ratio:.2f} based on a sample size of {sample_size}.

Explain what this means to the user in 2-4 sentences.
STRICT CONSTRAINTS:
- DO NOT use the word "discrimination". Use "statistical indication of bias".
- DO NOT calculate anything.
- DO NOT generate new statistics or numbers. 
- Only explain that this disparity indicates lower relative approval rates compared to references.
"""
    try:
        model = genai.GenerativeModel("gemini-2.5-flash") # Use gemini-2.5-flash which is standard and fast
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini error: {e}")
        return "An error occurred while generating the explanation."

def generate_org_recommendation(domain: str, flagged_slices: list) -> str:
    if not flagged_slices:
        return "No statistical indications of bias were detected."
        
    if os.getenv("GEMINI_API_KEY") is None:
        return "Simulated Gemini Response: Focus immediate reviews on the processes affecting the high-priority flagged slices. We recommend standardizing evaluation criteria and ensuring adequate oversight."

    slices_summary = ""
    for s in flagged_slices[:3]:
        slices_summary += f"- Slice: {s['sex']} {s['race']} {s['age_group']}, Disparity: {s['disparity_ratio']:.2f}, Note: {s['remediation_note']}\n"
    
    prompt = f"""
You are an advisory expert on algorithmic fairness and auditing.
An organization ran a bias audit in the domain '{domain}'. 
The following top priority slices were flagged with a statistical indication of bias:

{slices_summary}

Provide a 2-3 sentence recommendation for the organization on how to approach these indications.
STRICT CONSTRAINTS:
- DO NOT use the word "discrimination". Use "statistical indication of bias".
- DO NOT calculate anything.
- DO NOT generate any numbers or stats.
- Only rephrase the provided notes into an actionable advisory sentiment.
"""
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Gemini error: {e}")
        return "An error occurred while generating the recommendation."
