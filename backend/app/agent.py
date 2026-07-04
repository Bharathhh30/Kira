# ruff: noqa: E402
import logging
import asyncio
import httpx
import os
from collections.abc import AsyncIterable
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=env_path)

from livekit import rtc
from livekit.agents import JobContext, WorkerOptions, cli, AutoSubscribe
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import cartesia
from livekit.agents.inference import STT, TTS
from app.core.security import create_access_token
from livekit.agents import stt, tts, llm

logger = logging.getLogger("kira-voice-agent")

BASE_URL = "http://localhost:8000"


class KiraInterviewAgent(Agent):
    """Voice agent that drives the Kira interview state machine via REST calls."""

    def __init__(self, interview_id: str, user_id: str) -> None:
        self.interview_id = interview_id
        self.user_id = user_id
        self.access_token = create_access_token(subject=user_id)
        self.is_completed = False
        # Queue used to pass the next question from on_user_turn_completed → llm_node
        self._response_queue: asyncio.Queue[str] = asyncio.Queue()
        self._session: AgentSession | None = None

        super().__init__(instructions="You are Kira, an AI technical interviewer.")

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}"}

    async def get_current_question(self) -> str:
        async with httpx.AsyncClient() as client:
            try:
                url = f"{BASE_URL}/api/interview/state/{self.interview_id}"
                resp = await client.get(url, headers=self._auth_headers())
                if resp.status_code == 200:
                    data = resp.json()
                    self.is_completed = data.get("is_completed", False)
                    return data.get("current_question") or "Tell me about yourself."
                logger.error(f"State endpoint returned {resp.status_code}")
            except Exception:
                logger.exception("Error fetching interview state")
        return "Tell me about yourself and your experience."

    async def submit_answer_and_get_next(self, answer: str) -> str:
        async with httpx.AsyncClient() as client:
            try:
                url = f"{BASE_URL}/api/interview/next/{self.interview_id}"
                resp = await client.post(
                    url, json={"answer": answer}, headers=self._auth_headers()
                )
                if resp.status_code == 200:
                    data = resp.json()
                    self.is_completed = data.get("is_completed", False)
                    if self.is_completed:
                        return "Thank you for completing the mock interview. You did great. Good luck!"
                    return data.get("current_question") or "Thank you, please continue."
                logger.error(f"Next endpoint returned {resp.status_code}")
            except Exception:
                logger.exception("Error submitting answer")
        return "I had trouble processing that. Could you repeat your answer?"

    async def on_user_turn_completed(
        self,
        turn_ctx: llm.ChatContext,
        new_message: llm.ChatMessage,
    ) -> None:
        """Called after each user turn ends. Submit answer and queue the next question."""
        user_text = ""
        if hasattr(new_message, "content"):
            content = new_message.content
            if isinstance(content, str):
                user_text = content
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, str):
                        user_text += part

        if not user_text.strip():
            logger.warning("Empty user transcript, skipping submission.")
            self._response_queue.put_nowait("")
            return

        logger.info(f"User answered: '{user_text}'")
        next_question = await self.submit_answer_and_get_next(user_text)
        logger.info(f"Next question: '{next_question}'")

        # Put the next question in the queue — llm_node will pick it up
        self._response_queue.put_nowait(next_question)

    async def llm_node(
        self,
        chat_ctx: llm.ChatContext,
        tools: list,
        model_settings: object,
    ) -> AsyncIterable[llm.ChatChunk | str]:
        """Wait for the state machine to provide the next question and yield it."""
        try:
            # Wait up to 15s for on_user_turn_completed to put the next question
            next_q = await asyncio.wait_for(self._response_queue.get(), timeout=15.0)
        except asyncio.TimeoutError:
            logger.error("Timed out waiting for next question from state machine.")
            next_q = "I'm sorry, I had a technical issue. Could you please repeat?"

        if next_q:
            yield next_q


async def entrypoint(ctx: JobContext):
    logger.info(f"Connecting room: {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for candidate participant
    logger.info("Waiting for candidate to join...")
    candidate: rtc.RemoteParticipant | None = None
    for p in ctx.room.remote_participants.values():
        if p.identity.startswith("user-"):
            candidate = p
            break

    if not candidate:
        joined_event = asyncio.Event()

        @ctx.room.on("participant_connected")
        def on_participant_connected(p: rtc.RemoteParticipant) -> None:
            nonlocal candidate
            if p.identity.startswith("user-"):
                candidate = p
                joined_event.set()

        try:
            await asyncio.wait_for(joined_event.wait(), timeout=30)
        except asyncio.TimeoutError:
            logger.error("No candidate joined within 30 seconds. Exiting.")
            return

    user_id = candidate.identity.replace("user-", "")  # type: ignore[union-attr]
    logger.info(f"Candidate joined: user_id={user_id}")

    agent = KiraInterviewAgent(interview_id=str(ctx.room.name), user_id=user_id)

    session = AgentSession(
        stt=stt.FallbackAdapter(
            [
                STT.from_model_string("assemblyai/universal-streaming:en"),
                STT.from_model_string("deepgram/nova-3"),
            ]
        ),
        tts=tts.FallbackAdapter(
            [
                cartesia.TTS(
                    model="sonic-3",
                    voice="427a8721-3773-4d49-afa4-ee7c439c7bb7",
                ),
                TTS.from_model_string("deepgram/aura-asteria-en"),
            ]
        ),
    )
    agent._session = session

    await session.start(agent, room=ctx.room)
    logger.info("AgentSession started in room.")

    # Fetch and speak the first interview question immediately
    first_question = await agent.get_current_question()
    logger.info(f"Speaking first question: '{first_question}'")
    session.say(first_question, allow_interruptions=False)

    # Keep alive until room disconnects or interview completes
    while ctx.room.connection_state == rtc.ConnectionState.CONN_CONNECTED:
        if agent.is_completed:
            await asyncio.sleep(10)
            logger.info("Interview completed. Disconnecting.")
            await ctx.room.disconnect()
            break
        await asyncio.sleep(1)


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
