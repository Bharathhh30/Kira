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
        self._session: AgentSession | None = None
        # Start locked to block user turn processing during agent initialization and first question playout
        self._is_processing_turn = True

        super().__init__(instructions="You are Kira, an AI technical interviewer.")

    def enable_turn_processing(self) -> None:
        """Unlock turn processing to allow candidate answers."""
        self._is_processing_turn = False
        logger.info(
            "Turn processing enabled: Kira is now listening for candidate response."
        )

    def disable_turn_processing(self) -> None:
        """Lock turn processing during speaking or background API requests."""
        self._is_processing_turn = True
        logger.info("Turn processing disabled.")

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
        """Called after each user turn ends. Submit answer and speak the next question."""
        if self.is_completed:
            logger.info("Interview is already completed. Skipping processing.")
            return

        if self._is_processing_turn:
            logger.info(
                "Ignoring user turn callback because agent is currently speaking or processing."
            )
            return

        self._is_processing_turn = True
        try:
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
                return

            logger.info(f"User answered: '{user_text}'")
            next_question = await self.submit_answer_and_get_next(user_text)
            logger.info(f"Next question: '{next_question}'")

            if self._session:
                # Speak the question directly and prevent early interruption
                parts = next_question.split("|||")
                spoken_question = parts[0].strip()
                if len(parts) > 1 and parts[1].strip():
                    spoken_question += (
                        " Please refer to the code snippet displayed on your screen."
                    )
                handle = self._session.say(spoken_question, allow_interruptions=False)
                # Wait for the agent to finish speaking before releasing the lock
                await handle.wait_for_playout()
        finally:
            self._is_processing_turn = False

    async def llm_node(
        self,
        chat_ctx: llm.ChatContext,
        tools: list,
        model_settings: object,
    ) -> AsyncIterable[llm.ChatChunk | str]:
        """No-op LLM generator as we drive speech explicitly via session.say."""
        if False:
            yield ""


async def entrypoint(ctx: JobContext):
    logger.info(f"Connecting room: {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait a brief moment to allow the participant list to sync completely
    await asyncio.sleep(1.0)

    # Prevent overlapping agent instances by consensus on identity sort order
    my_identity = ctx.room.local_participant.identity
    other_participants = [
        (p.identity, p.name) for p in ctx.room.remote_participants.values()
    ]
    logger.info(f"My agent identity: '{my_identity}'")
    logger.info(f"Other participants in room: {other_participants}")

    other_agents = [
        p.identity
        for p in ctx.room.remote_participants.values()
        if not p.identity.startswith("user-")
    ]
    if other_agents:
        all_agents = sorted([my_identity] + other_agents)
        logger.info(f"All agents list: {all_agents}")
        if my_identity != all_agents[0]:
            logger.warning(
                f"Another agent ({all_agents[0]}) has priority in room {ctx.room.name}. Exiting to prevent overlap."
            )
            return
        else:
            # We have priority! Proactively kick out all other ghost agents to prevent overlaps and double voices.
            from livekit import api as lk_api_mod

            lk_api = lk_api_mod.LiveKitAPI(
                url=os.getenv("LIVEKIT_URL") or "",
                api_key=os.getenv("LIVEKIT_API_KEY") or "",
                api_secret=os.getenv("LIVEKIT_API_SECRET") or "",
            )
            async with lk_api:
                for agent_id in other_agents:
                    try:
                        logger.info(
                            f"Proactively removing ghost agent {agent_id} from room {ctx.room.name}..."
                        )
                        await lk_api.room.remove_participant(
                            lk_api_mod.RoomParticipantIdentity(
                                room=ctx.room.name, identity=agent_id
                            )
                        )
                    except Exception as re:
                        logger.warning(f"Failed to remove ghost agent {agent_id}: {re}")

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
                TTS.from_model_string(
                    "cartesia/sonic-3:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"
                ),
                cartesia.TTS(
                    model="sonic-3",
                    voice="427a8721-3773-4d49-afa4-ee7c439c7bb7",
                ),
                TTS.from_model_string("deepgram/aura-asteria-en"),
            ]
        ),
        min_endpointing_delay=2.0,
        max_endpointing_delay=4.0,
        false_interruption_timeout=1.5,
        min_interruption_duration=1.0,
    )
    agent._session = session

    await session.start(agent, room=ctx.room)
    logger.info("AgentSession started in room.")

    # Fetch and speak the first interview question immediately in a background task
    # to avoid blocking the LiveKit connection handshake.
    async def speak_first_question():
        first_question = await agent.get_current_question()
        logger.info(f"Speaking first question: '{first_question}'")
        parts = first_question.split("|||")
        spoken_question = parts[0].strip()
        if len(parts) > 1 and parts[1].strip():
            spoken_question += (
                " Please refer to the code snippet displayed on your screen."
            )
        handle = session.say(spoken_question, allow_interruptions=False)
        await handle.wait_for_playout()
        agent.enable_turn_processing()

    asyncio.create_task(speak_first_question())

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
