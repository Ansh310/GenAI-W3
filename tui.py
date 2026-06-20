"""
TUIAgent — Week 3 Textual UI

Usage:
    python agent.py --tui
"""

try:
    from textual import App, ComposeResult
except ImportError:
    from textual.app import App, ComposeResult

from textual.containers import (
    Vertical,
    Horizontal,
)
from textual.widgets import (
    Header,
    Footer,
    Input,
    Static,
    RichLog,
)

from agent import Agent


class TUIAgent(Agent):
    """
    Agent + tool logging hook.
    """

    def __init__(
        self,
        app,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )
        self.app = app

    def _emit(
        self,
        event,
        **data,
    ):
        if event == "tool_call":

            name = data.get(
                "name",
                "unknown",
            )

            self.app.log_tool(
                f"[tool] {name}"
            )


class ResearchDeskApp(App):

    CSS = """
    Screen {
        layout: vertical;
    }

    #chat {
        height: 1fr;
        border: solid green;
    }

    #tools {
        height: 10;
        border: solid yellow;
    }

    #input {
        dock: bottom;
    }
    """

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+l", "clear_chat", "Clear Chat"),
        ("ctrl+k", "clear_tools", "Clear Tools"),
    ]

    def compose(
        self,
    ) -> ComposeResult:

        yield Header()

        with Vertical():

            yield RichLog(
                id="chat",
                markup=True,
                wrap=True,
            )

            yield RichLog(
                id="tools",
                markup=True,
                wrap=True,
            )

            yield Input(
                placeholder=
                "Ask Research Desk...",
                id="input",
            )

        yield Footer()

    def on_mount(self):

        self.chat_log = (
            self.query_one(
                "#chat",
                RichLog,
            )
        )

        self.tool_log = (
            self.query_one(
                "#tools",
                RichLog,
            )
        )

        self.input_box = (
            self.query_one(
                "#input",
                Input,
            )
        )

        self.agent = TUIAgent(
            app=self,
        )

        self.chat_log.write(
            f"Research Desk "
            f"[{self.agent.session_id}]"
        )

    def log_tool(
        self,
        message,
    ):
        self.tool_log.write(
            message
        )

    async def on_input_submitted(
        self,
        event: Input.Submitted,
    ):

        user_text = (
            event.value.strip()
        )

        if not user_text:
            return

        self.input_box.value = ""

        self.chat_log.write(
            f"[b cyan]You:[/b cyan] "
            f"{user_text}"
        )

        self.run_worker(
            self.run_agent(
                user_text
            )
        )

    async def run_agent(
        self,
        prompt,
    ):

        try:

            answer = (
                self.agent.chat(
                    prompt
                )
            )

        except Exception as e:

            answer = (
                f"Error: {e}"
            )

        self.chat_log.write(
            f"[b green]Agent:[/b green] "
            f"{answer}"
        )

    def action_clear_chat(
        self,
    ):
        self.chat_log.clear()

    def action_clear_tools(
        self,
    ):
        self.tool_log.clear()


def main():

    app = ResearchDeskApp()

    app.run()


if __name__ == "__main__":
    main()