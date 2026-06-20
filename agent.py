import os
import sys
import json
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from openai import OpenAI

from tools.files import (
    read_file,
    write_file,
    edit_file,
    list_files,
)

from tools.web import (
    web_search,
    web_fetch,
)

from tools.papers import (
    paper_search,
    read_paper,
)

load_dotenv()

MODEL = "openai/gpt-4o-mini"
MAX_ITERATIONS = 10

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

SESSIONS_DIR = ".agent/sessions"
AGENTS_MD = "AGENTS.md"

BASE_PROMPT = """
You are Research Desk.

You are a research assistant with:
- Web search
- Web page reading
- Paper search
- Paper reading
- File editing

Follow AGENTS.md rules carefully.
"""


def ensure_dirs():
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    os.makedirs("notes", exist_ok=True)


def create_session():
    ensure_dirs()
    return uuid.uuid4().hex[:8]


def save_session(session_id, messages, title="Untitled"):
    ensure_dirs()

    data = {
        "id": session_id,
        "title": title,
        "updated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "messages": messages,
    }

    path = os.path.join(
        SESSIONS_DIR,
        f"{session_id}.json",
    )

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False,
        )


def load_session(session_id):
    path = os.path.join(
        SESSIONS_DIR,
        f"{session_id}.json",
    )

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_system_prompt():

    prompt = BASE_PROMPT

    if os.path.exists(AGENTS_MD):
        with open(
            AGENTS_MD,
            "r",
            encoding="utf-8",
        ) as f:
            prompt += "\n\n" + f.read()

    return prompt

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read file contents",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "start_line": {"type": "integer"},
                    "read_lines": {"type": "integer"},
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": [
                    "path",
                    "content",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Edit a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "operation": {
                        "type": "string"
                    },
                    "start_line": {
                        "type": "integer"
                    },
                    "end_line": {
                        "type": "integer"
                    },
                    "content": {
                        "type": "string"
                    },
                },
                "required": [
                    "path",
                    "operation",
                    "start_line",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "pattern": {
                        "type": "string"
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search web",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string"
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": "Fetch webpage",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"}
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "paper_search",
            "description": "Search papers",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string"
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_paper",
            "description": "Read paper",
            "parameters": {
                "type": "object",
                "properties": {
                    "arxiv_id": {
                        "type": "string"
                    }
                },
                "required": ["arxiv_id"],
            },
        },
    },
]

class Agent:

    def __init__(
        self,
        session_id=None,
    ):

        ensure_dirs()

        if session_id:

            session = load_session(
                session_id
            )

            self.session_id = session_id
            self.messages = session[
                "messages"
            ]

        else:

            self.session_id = (
                create_session()
            )

            self.messages = [
                {
                    "role": "system",
                    "content":
                    build_system_prompt(),
                }
            ]

    def chat(
        self,
        user_message,
    ):

        self.messages.append(
            {
                "role": "user",
                "content": user_message,
            }
        )

        answer = self._run_loop()

        save_session(
            self.session_id,
            self.messages,
            title=f"Session {self.session_id}",
        )

        return answer

    def run_once(
        self,
        prompt,
    ):
        return self.chat(prompt)

    def dispatch(
        self,
        tool_call,
    ):

        name = tool_call.function.name

        args = json.loads(
            tool_call.function.arguments
        )

        mapping = {
            "read_file":
                read_file,
            "write_file":
                write_file,
            "edit_file":
                edit_file,
            "list_files":
                list_files,
            "web_search":
                web_search,
            "web_fetch":
                web_fetch,
            "paper_search":
                paper_search,
            "read_paper":
                read_paper,
        }

        if name not in mapping:
            return json.dumps(
                {
                    "error":
                    f"Unknown tool {name}"
                }
            )

        result = mapping[name](**args)

        return json.dumps(result)

    def _emit(
        self,
        event,
        **data,
    ):
        pass

    def _run_loop(self):

        for _ in range(
            MAX_ITERATIONS
        ):

            response = (
                client.chat.completions.create(
                    model=MODEL,
                    messages=self.messages,
                    tools=TOOLS,
                )
            )

            message = (
                response
                .choices[0]
                .message
            )

            if not message.tool_calls:

                content = (
                    message.content
                    or ""
                )

                self.messages.append(
                    {
                        "role":
                        "assistant",
                        "content":
                        content,
                    }
                )

                return content

            self.messages.append(
    {
        "role": "assistant",
        "content": message.content,
        "tool_calls": [
            {
                "id": tc.id,
                "type": tc.type,
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            for tc in message.tool_calls
        ],
    }
)

            for tool_call in (
                message.tool_calls
            ):

                self._emit(
                    "tool_call",
                    name=
                    tool_call.function.name,
                )

                result = (
                    self.dispatch(
                        tool_call
                    )
                )

                self.messages.append(
                    {
                        "role":
                        "tool",
                        "tool_call_id":
                        tool_call.id,
                        "content":
                        result,
                    }
                )

        return (
            "Maximum iterations reached."
        ) 
class REPLAgent(
    Agent
):

    def _emit(
        self,
        event,
        **data,
    ):

        if event == "tool_call":

            print(
                f"[tool] "
                f"{data['name']}",
                file=sys.stderr,
            )

    def run(self):

        print(
            f"Research Desk "
            f"[{self.session_id}]"
        )

        while True:

            try:

                user_input = (
                    input("> ")
                    .strip()
                )

            except (
                EOFError,
                KeyboardInterrupt,
            ):
                print()
                break

            if (
                not user_input
                or user_input
                in [
                    "/quit",
                    "/exit",
                ]
            ):
                break

            print(
                self.chat(
                    user_input
                )
            )
            print()


def main():

    session_id = None

    if "--session" in sys.argv:

        idx = sys.argv.index(
            "--session"
        )

        session_id = (
            sys.argv[idx + 1]
        )

        del sys.argv[idx:idx+2]

    agent = REPLAgent(
        session_id=session_id
    )

    if len(sys.argv) > 1:

        prompt = " ".join(
            sys.argv[1:]
        )

        print(
            agent.run_once(
                prompt
            )
        )

        return

    agent.run()


if __name__ == "__main__":
    main()   

