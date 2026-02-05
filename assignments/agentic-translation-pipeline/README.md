
# Project Setup and Usage

Follow the steps below to set up the environment, run the backend services, and configure the LangGraph agent parameters.

## 1. Installation

Choose one of the following methods to install the necessary dependencies.

### Option A: Using Conda (Recommended)

If you are using Anaconda or Miniconda, create the environment using the provided YAML file:

```bash
conda env create -f environment.yaml
conda activate agentic-translate

```

### Option B: Using Pip

If you prefer standard Python virtual environments or a direct Pip install:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt

```

---

## 2. Running the Application

You will need to open **two separate terminal windows** to run the project components simultaneously.

### Terminal 1: Root Service

In your first terminal, from the root directory of the project, run:

```bash
python main.py

```

### Terminal 2: LangGraph Agent

In your second terminal, navigate to the agent directory and execute the script:

```bash
cd langgraphAgent
python main.py

```

---

## 3. Configuration & Testing

To test different scenarios or languages, you can modify the entry point file located at `langgraphAgent/main.py`.

### Changing Session ID

To start a new conversation thread or resume a specific one, locate the `run_workflow` function and modify the `session_id`:

```python
# Inside langgraphAgent/main.py
def run_workflow(...):
    ...
    config = {"configurable": {"thread_id": "YOUR_SESSION_ID_HERE"}}

```

### Changing User Input

To change the query being sent to the agent, modify the input in the execution block at the **bottom of the file**:

```python
# Last lines of langgraphAgent/main.py
if __name__ == "__main__":
   asyncio.run(run_workflow("USER INPUT", "Hindi"))

```

### Language Codes

If you need to supply a specific language the input, please refer to **`langCodes.json`** for the supported languages.