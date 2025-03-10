from huggingface_hub import InferenceClient
import os
from dotenv import load_dotenv

load_dotenv()
# For production, consider removing or securing this log.
print("Environment Keys Loaded:", os.getenv('HUGGINGFACE_API_KEY'))

hf_api_key = os.getenv('HUGGINGFACE_API_KEY')
if not hf_api_key:
    raise ValueError("Hugging Face API Key not set in environment variable")

# Initialize the Inference Client with your desired model.
text_generation_client = InferenceClient(token=hf_api_key, model="mistralai/Mistral-Nemo-Instruct-2407")

def format_prompt_for_model(user_prompt):
    # Update the system context to instruct the model on sustainability assessment.
    system_context_prompt = (
        ""
    )
    combined_prompt = f"<s>[SYS] {system_context_prompt} [/SYS]\n[INST] {user_prompt} [/INST]"
    return combined_prompt

def generate_sustainability_assessment(
    prompt,
    creativity_level=0.2,
    max_tokens_to_generate=1024,
    top_p_filtering_ratio=0.96,
    repetition_penalty=1.0,
):
    creativity_level = float(creativity_level)
    if creativity_level < 1e-2:
        creativity_level = 1e-2
    top_p_filtering_ratio = float(top_p_filtering_ratio)

    generation_parameters = dict(
        temperature=creativity_level,
        max_new_tokens=max_tokens_to_generate,
        top_p=top_p_filtering_ratio,
        repetition_penalty=repetition_penalty,
        do_sample=True,
        seed=42,
    )

    model_ready_prompt = format_prompt_for_model(prompt)
    generated_text_stream = text_generation_client.text_generation(
        model_ready_prompt,
        **generation_parameters,
        stream=True,
        details=True,
        return_full_text=True
    )

    final_output_text = ""
    for text_segment in generated_text_stream:
        final_output_text += text_segment.token.text

    return final_output_text