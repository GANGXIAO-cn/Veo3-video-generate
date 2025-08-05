import streamlit as st
import asyncio
import os
from typing import Dict, Any
from prompt_library import PROMPT_LIBRARY
from main import run_workflow
import json

# Configure the Streamlit page
st.set_page_config(
    page_title="AI Video Generator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

def set_api_keys(kie_token: str, openrouter_key: str):
    """Set API keys as environment variables"""
    if kie_token:
        os.environ["KIE_API_TOKEN"] = kie_token
    if openrouter_key:
        os.environ["OPENROUTER_API_KEY"] = openrouter_key

def validate_api_keys() -> bool:
    """Check if required API keys are set"""
    return bool(os.environ.get("KIE_API_TOKEN")) and bool(os.environ.get("OPENROUTER_API_KEY"))

def display_video(video_url: str, title: str):
    """Display the generated video"""
    if video_url:
        st.success("✅ Video generated successfully!")
        st.subheader(f"🎬 {title}")
        
        # Display video player
        st.video(video_url)
        
        # Provide download link
        st.markdown(f"**Direct link:** [Download Video]({video_url})")
    else:
        st.error("❌ Failed to generate video or no video URL returned")

def main():
    # Sidebar for API keys
    with st.sidebar:
        st.header("🔑 API Configuration")
        st.markdown("Enter your API keys to get started:")
        
        kie_token = st.text_input(
            "KIE API Token",
            type="password",
            help="Your KIE AI API token for VEO3 video generation"
        )
        
        openrouter_key = st.text_input(
            "OpenRouter API Key", 
            type="password",
            help="Your OpenRouter API key for GPT-4 access"
        )
        
        if st.button("Save", type="primary"): 
            set_api_keys(kie_token, openrouter_key)
            if validate_api_keys():
                st.success("✅ API keys saved successfully!")
            else:
                st.error("❌ Please provide both API keys")

    # Main content area
    st.title("🎬 AI Video Generator")
    st.markdown("Generate stunning videos using AI with customizable prompts and settings")

    # Check if API keys are configured
    if not validate_api_keys():
        st.warning("⚠️ Please configure your API keys in the sidebar before proceeding.")
        st.stop()

    # Video idea input
    st.header("💡 Video Idea")
    video_idea = st.text_area(
        "Describe your video concept:",
        placeholder="e.g., I want an ad for a Mercedes car showing luxury and performance",
        height=100
    )

    # Prompt inspiration selection
    st.header("🎨 Prompt Inspiration")
    st.markdown("Choose one or more prompt templates to inspire your video:")
    
    # Create a more user-friendly prompt selection
    prompt_options = []
    for i, prompt in enumerate(PROMPT_LIBRARY):
        prompt_options.append({
            "index": i,
            "display": f"{prompt['name']} - {prompt['description'][:100]}{'...' if len(prompt['description']) > 100 else ''}",
            "name": prompt['name'],
            "description": prompt['description']
        })
    
    # Single select for prompts
    selected_prompt_display = st.selectbox(
        "Select prompt inspiration:",
        options=[opt["display"] for opt in prompt_options],
        help="Choose one prompt template to inspire your video"
    )
    
    # Get selected prompt
    selected_prompt = None
    if selected_prompt_display:
        for opt in prompt_options:
            if opt["display"] == selected_prompt_display:
                selected_prompt = PROMPT_LIBRARY[opt["index"]]
                break

    # Display selected prompt details
    if selected_prompt:
        st.subheader("📋 Selected Prompt Details")
        with st.expander(f"🎯 {selected_prompt['name']}"):
            st.markdown(f"**Description:** {selected_prompt['description']}")
            st.markdown(f"**Source:** {selected_prompt['source']}")
            
            # Show a preview of the prompt structure
            if isinstance(selected_prompt['prompt'], dict):
                st.json(selected_prompt['prompt'], expanded=False)

    # Video settings
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("📐 Resolution")
        aspect_ratio = st.selectbox(
            "Choose aspect ratio:",
            options=["16:9", "9:16"],
            help="16:9 for landscape videos, 9:16 for vertical/mobile videos"
        )
    
    with col2:
        st.header("🚀 Model")
        model = st.selectbox(
            "Choose VEO3 model:",
            options=["veo3_fast", "veo3"],
            help="veo3_fast is cheaper and faster, veo3 provides higher quality"
        )

    # Generate button
    st.markdown("---")
    
    if not video_idea.strip():
        st.warning("⚠️ Please enter a video idea to proceed.")
    elif not selected_prompt:
        st.warning("⚠️ Please select a prompt inspiration.")
    else:
        if st.button("🎬 Generate Video", type="primary", use_container_width=True):
            # Use the selected prompt
            inspiration_prompt = selected_prompt['prompt']
            
            # Prepare inputs for the workflow
            inputs = {
                "ad_idea": video_idea,
                "inspiration_prompt": inspiration_prompt,
                "aspect_ratio": aspect_ratio,
                "model": model
            }
            print(f"Inputs: {inputs}")
            
            # Show progress
            with st.spinner("🔄 Generating your video... This may take several minutes."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # Update progress
                    progress_bar.progress(10)
                    status_text.text("📝 Creating video prompt...")
                    
                    # Run the workflow
                    result = asyncio.run(run_workflow(inputs))
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Video generation completed!")
                    
                    if result:
                        # Display the result
                        st.balloons()
                        display_video(result.get("video_url"), result.get("title", "Generated Video"))
                        
                        # Show generated prompt details
                        with st.expander("📄 Generated Prompt Details"):
                            st.markdown(f"**Title:** {result.get('title', 'N/A')}")
                            st.markdown("**Generated Prompt:**")
                            st.text_area("", value=result.get('prompt', 'N/A'), height=200, disabled=True)
                    else:
                        st.error("❌ Failed to generate video. Please check the logs for more details.")
                        
                except Exception as e:
                    st.error(f"❌ An error occurred: {str(e)}")
                    st.markdown("Please check your API keys and try again.")
                
                finally:
                    progress_bar.empty()
                    status_text.empty()

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            <p>🎬 AI Video Generator powered by VEO3</p>
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
