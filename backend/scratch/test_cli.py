import sys
import os
import uuid

# Add the backend/ directory to sys.path so we can import app modules directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.interview.context_loader import ContextLoader
from app.services.interview.manager import InterviewManager

# Mock Resume JSON matching the schema of our Profile
MOCK_RESUME = {
    "personal": {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "location": "San Francisco, CA",
        "summary": "Experienced Full Stack Engineer specialized in Python and React.",
    },
    "skills": {
        "technical": ["Python", "FastAPI", "React", "TypeScript"],
        "tools": ["Docker", "PostgreSQL", "Git"],
    },
    "experience": [
        {
            "company": "Tech Corp",
            "title": "Software Engineer",
            "start_date": "2023-01",
            "end_date": "Present",
            "bullets": [
                "Built high-performance APIs using FastAPI and Python.",
                "Optimized database queries in PostgreSQL, reducing latency by 30%.",
            ],
        }
    ],
    "projects": [
        {
            "name": "E-Commerce System",
            "description": "A microservices-based shop built using Docker, Python, and React.",
            "technologies": ["Python", "React", "Docker"],
        }
    ],
}


def main():
    print("==================================================")
    print("       Kira Interview Engine CLI Simulator        ")
    print("==================================================")

    user_id = uuid.uuid4()

    # 1. Load context (Step 2)
    state = ContextLoader.load_context(
        user_id=user_id, resume_json=MOCK_RESUME, interview_mode="resume"
    )

    # Checkpoint Step 1: Print state and verify initialization
    print("\n--- STEP 1 & 2 CHECKPOINT: Initialized Interview State ---")
    print(f"Interview ID:    {state.interview_id}")
    print(f"User ID:         {state.user_id}")
    print(f"Interview Mode:  {state.interview_mode}")
    print(f"Current Topic:   {state.current_topic}")
    print(f"Remaining Topics:{state.remaining_topics}")
    print(f"Remaining Time:  {state.remaining_time} seconds")
    print(f"First Question:  {state.current_question}")
    print("----------------------------------------------------------\n")

    manager = InterviewManager()

    # 2. Run the interview loop (Step 4 Checkpoint)
    print("Starting interview session. Type your response below.")
    print("Type 'exit' to quit the simulation early.")
    print("==================================================\n")

    while not state.is_completed:
        print(f"\n[AI] Question: {state.current_question}")
        try:
            answer = input("\n[Candidate] Answer: ")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting simulation.")
            break

        if answer.strip().lower() == "exit":
            print("Exiting simulation.")
            break

        print("\n[Engine] Processing answer...")
        result = manager.process_answer(state, answer)

        print("\n--- Transition details ---")
        print(f"Action:       {result['action']}")
        print(
            f"Evaluation:   Score={result['evaluation']['score']} | Reason: {result['evaluation']['reason']}"
        )
        print(f"Follow-up:    Count={state.follow_up_count}")
        print(f"Remaining:    Topics Count={len(state.remaining_topics)}")

        if result["action"] == "END":
            print("\n==================================================")
            print("              Interview Completed                 ")
            print("==================================================")
            break

    print("\nFinal History:")
    for i, entry in enumerate(state.history, 1):
        print(f"\nTurn {i}:")
        print(f"  Q: {entry.question}")
        print(f"  A: {entry.answer}")
        print(f"  Score: {entry.score}")
        print(f"  Feedback: {entry.feedback}")


if __name__ == "__main__":
    main()
