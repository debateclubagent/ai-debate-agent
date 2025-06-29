# AI Debate Agent

This repository contains a Streamlit application that demonstrates a simple "whiteboard" interface. Users can input a question and the app generates responses using the Six Thinking Hats approach. Each question is shown as a set of cards (Yellow, Black and Blue hat) so multiple questions can be displayed on the board.

## Running locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set `DEEPSEEK_API_KEY` in Streamlit secrets (e.g. `/.streamlit/secrets.toml`).
3. Run the application:
   ```bash
   streamlit run whiteboard_app.py
   ```

The original demo `streamlit_app.py` is still available for generating a single set of hat responses.
