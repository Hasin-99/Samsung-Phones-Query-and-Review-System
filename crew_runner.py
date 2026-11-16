from crewai import Crew, Process, Task
from agents import spec_retriever, review_writer


def generate_review(phone_name: str) -> str:
    spec_task = Task(
        description=(
            f"Fetch the full specifications for the phone '{phone_name}' "
            f"by calling the fetch_phone_specs tool with phone_name='{phone_name}'. "
            "Return the raw spec block exactly as the tool returned it."
        ),
        expected_output="A structured block starting with 'Phone:' followed by lines for display, chipset, camera, battery, etc.",
        agent=spec_retriever,
    )

    write_task = Task(
        description=(
            f"Write a 300-400 word product review of '{phone_name}'. "
            "Use ONLY the specifications returned by the previous task. "
            "Structure: (1) one-sentence intro naming the phone, "
            "(2) paragraph on display + design, "
            "(3) paragraph on camera, "
            "(4) paragraph on performance + battery, "
            "(5) final verdict with target audience. "
            "Do not invent specs. If a value is missing, omit it."
        ),
        expected_output="A well-structured review in plain text, 300-400 words.",
        agent=review_writer,
        context=[spec_task],
    )

    crew = Crew(
        agents=[spec_retriever, review_writer],
        tasks=[spec_task, write_task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()
    return str(result)


if __name__ == "__main__":
    import sys
    phone = " ".join(sys.argv[1:]) or "Samsung Galaxy S23"
    print("=" * 70)
    print(f"Generating review for: {phone}")
    print("=" * 70)
    review = generate_review(phone)
    print("=" * 70)
    print("FINAL REVIEW")
    print("=" * 70)
    print(review)
