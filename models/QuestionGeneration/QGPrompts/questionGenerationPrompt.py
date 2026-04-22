from langchain.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate

examples = [
    {
        "Question_Type": "T/F",
        "Context":  "In computer networks, TCP (Transmission Control Protocol) and UDP (User Datagram Protocol) are two transport layer protocols used for sending data over the Internet. TCP is connection-oriented, meaning it establishes a connection before data can be sent and ensures all data arrives correctly and in order. It includes error-checking, acknowledgment of data, and retransmission of lost packets. UDP, on the other hand, is connectionless. It does not establish a connection before sending data and does not guarantee delivery or that packets will arrive in the same order they were sent. UDP has less overhead and is therefore faster than TCP, making it suitable for time-sensitive applications where occasional data loss is acceptable.",
        "Question": "TCP guarantees that data packets will be delivered in the same order they were sent, while UDP does not provide this guarantee.",
        "Answer": "True",
        "Options": None,
        "Explanation": "According to the context, TCP ensures ordered delivery while UDP provides no such guarantee."
    },
    {
        "Question_Type": "MCQ",
        "Context": "Object-oriented programming (OOP) is a programming paradigm based on the concept of 'objects', which can contain data and code: data in the form of fields (attributes or properties), and code in the form of methods. The four main principles of OOP are encapsulation, inheritance, polymorphism, and abstraction.",
        "Question": "Which of the following is NOT one of the four main principles of Object-Oriented Programming?",
        "Options": [
            "A. Encapsulation",
            "B. Inheritance",
            "C. Compilation",
            "D. Polymorphism"
        ],
        "Answer": "C",
        "Explanation": "Compilation is not one of the four OOP principles; the correct principles are encapsulation, inheritance, polymorphism, and abstraction."
    }
]

few_shot_prompt = FewShotChatMessagePromptTemplate(
    example_prompt=ChatPromptTemplate.from_messages([
        ("user", "Question Type: {Question_Type}, Context: {Context}"),
        ("ai", "Question: {Question}\nOptions: {Options}\nAnswer: {Answer}\nExplanation: {Explanation}\n")
    ]),
    examples=examples
)

QuestionGenPrompt = ChatPromptTemplate.from_messages([
    ("system", """
You are an expert question-generation assistant. Your goal is to generate **high-quality educational questions** using the context provided by the user.

## Supported Question Types:
- MCQ (Multiple Choice Question)
- T/F (True/False)

## General Rules:
- Generate **exactly one question**.
- The question **must match the question type** specified by the user.
- The question must be **fully answerable using the context only**.
- Use clear, academically appropriate language.
- Avoid ambiguity and trick questions.
- Produce output **following the exact structure** in the examples.

## MCQ Guidelines:
- Provide exactly 4 options (A, B, C, D).
- Only one option must be correct.
- Distractors must be plausible.
- Options should be similar in length and structure.

## True/False Guidelines:
- Statement must be clearly True or False.
- Avoid extreme terms unless supported by the context.

## Important Guidelines:
For MCQ questions:
    - ALWAYS return the options as a JSON array of strings, like:
        ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"]
Do NOT return options as a single string. Do not merge options.

## Output Format (must match exactly):
Question: <your generated question>
Question_Type: <the type of the question>
Options: <4 MCQ options as an array OR None>
Answer: <the correct answer>
Explanation: <why this answer is correct>
"""),
    ("system", """
    You generate structured MCQ and T/F questions.
    IMPORTANT:
    - For MCQ: return options as a JSON array of strings. Example:
    ["A. ...", "B. ...", "C. ...", "D. ..."]
    - For T/F: set options to null.
    When producing MCQ options, ALWAYS return:
    "options": ["A. ...", "B. ...", "C. ...", "D. ..."]
    Never return them as a single string, a JSON stringified list, or combined text.
    """),

    few_shot_prompt,

    ("user", "Question Type: {question_type}, Context: {context}")
])