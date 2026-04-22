from langchain.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate

refiner_examples = [
        {
            "question_type": "MCQ",
            "context": "Binary search is an efficient algorithm for finding an item from a sorted list of items. It works by repeatedly dividing the search interval in half. If the value is less than the item in the middle of the interval, it narrows the interval to the lower half. Otherwise, it narrows it to the upper half. The search continues until the value is found or the interval is empty. Binary search has a time complexity of O(log n).",
            "question": "Binary search requires the data to be sorted before searching.",
            "answer": "False",
            "options": None,
            "explanation": "Binary search works on sorted data as mentioned in the transcript.",
            "feedback":(
                        "Advantages:\n"
                        "- Tests understanding of binary search prerequisites\n"
                        "Disadvantages:\n"
                        "- Answer is incorrect - should be True, not False\n"
                        "- Question format matches T/F but Answer contradicts transcript content\n"
                        "- Explanation contradicts the given Answer\n"
            )
        },
        {
            "question_type": "T/F",
            "context": "Arrays are data structures that store elements of the same type in contiguous memory locations. In most programming languages, array elements are accessed using an index, starting from 0. Arrays have fixed size once declared and provide O(1) access time to any element. Dynamic arrays, like Python lists or Java ArrayLists, can grow and shrink during runtime but may require reallocation of memory.",
            "question": "Which data structure provides the fastest element access?",
            "answer": "Arrays",
            "options": "A. Linked Lists\nB. Arrays\nC. Hash Tables\nD. Binary Trees",
            "explanation": "Arrays provide O(1) constant time access to elements using indices.",
            "feedback":(
                    "Advantages:\n"
                    "- Clear technical content about data structures\n\n"
                    "- Correct Answer is supported by transcript\n\n"
                    "Disadvantages:\n"
                    "- Question type mismatch - MCQ format used instead of T/F\n\n"
                    "- Answer format incorrect - should be True/False\n\n"
            )
        },
]
refiner_examples += [
    {
        "question_type": "MCQ",
        "context": "A stack is a linear data structure which follows the Last In First Out (LIFO) principle. Common operations include push (add), pop (remove), and peek (top element).",
        "question": "Which principle does a stack follow?",
        "answer": "A",
        "options": ["A. Last In First Out (LIFO)", "B. First In First Out (FIFO)", "C. Random Access", "D. Priority-based"],
        "explanation": "Stacks follow the LIFO principle, meaning the last element added is the first to be removed.",
        "feedback": "Advantages: tests understanding of stack operations. Disadvantages: none."
    },
    {
        "question_type": "T/F",
        "context": "In object-oriented programming, inheritance allows a class to acquire properties and methods of another class.",
        "question": "Inheritance allows a class to reuse code from another class.",
        "answer": "True",
        "options": None,
        "explanation": "By inheriting from another class, a subclass can reuse its methods and attributes.",
        "feedback": "Advantages: clear OOP concept. Disadvantages: none."
    },
    {
        "question_type": "MCQ",
        "context": "In Python, the 'dict' data type stores key-value pairs. Keys must be unique and immutable, and values can be any data type.",
        "question": "Which statement about Python dictionaries is correct?",
        "answer": "C",
        "options": [
            "A. Dictionary keys can be duplicated.",
            "B. Values must be immutable.",
            "C. Keys must be unique and immutable.",
            "D. Dictionaries maintain insertion order in all Python versions."
        ],
        "explanation": "Dictionary keys must be unique and immutable; values can be mutable.",
        "feedback": "Advantages: tests Python knowledge. Disadvantages: none."
    },
    {
        "question_type": "T/F",
        "context": "The quicksort algorithm is a divide-and-conquer sorting algorithm with an average time complexity of O(n log n).",
        "question": "Quicksort has an average time complexity of O(n log n).",
        "answer": "True",
        "options": None,
        "explanation": "Quicksort recursively partitions arrays and sorts them, achieving O(n log n) average complexity.",
        "feedback": "Advantages: clear fact-based T/F question. Disadvantages: none."
    },
    {
        "question_type": "MCQ",
        "context": "HTML elements can be nested within each other. Block-level elements start on a new line and can contain inline elements, while inline elements do not start on a new line.",
        "question": "Which of the following is a block-level HTML element?",
        "answer": "B",
        "options": ["A. <span>", "B. <div>", "C. <a>", "D. <img>"],
        "explanation": "<div> is a block-level element that starts on a new line and can contain other elements.",
        "feedback": "Advantages: tests understanding of HTML structure. Disadvantages: none."
    },
    {
        "question_type": "T/F",
        "context": "In relational databases, a primary key uniquely identifies each row in a table.",
        "question": "A table can have more than one primary key.",
        "answer": "False",
        "options": None,
        "explanation": "A table can have only one primary key, which uniquely identifies each record.",
        "feedback": "Advantages: reinforces database concept. Disadvantages: none."
    },
    {
        "question_type": "MCQ",
        "context": "CSS (Cascading Style Sheets) is used to control the style and layout of web pages. Properties like color, margin, and font-size define presentation.",
        "question": "Which property is used in CSS to change the font size?",
        "answer": "C",
        "options": ["A. color", "B. margin", "C. font-size", "D. background"],
        "explanation": "The 'font-size' property specifies the size of text in CSS.",
        "feedback": "Advantages: tests basic CSS knowledge. Disadvantages: none."
    }
]


refiner_examples += [
    {
        "question_type": "MCQ",
        "context": "In computer networks, the TCP (Transmission Control Protocol) ensures reliable communication by establishing a connection, acknowledging packets, and retransmitting lost data. UDP (User Datagram Protocol), in contrast, is connectionless and does not guarantee delivery.",
        "question": "UDP guarantees reliable delivery of packets over the network.",
        "answer": "False",
        "options": None,
        "explanation": "UDP is connectionless and does not provide reliability mechanisms like TCP does.",
        "feedback": (
            "Advantages:\n"
            "- Highlights key difference between TCP and UDP\n"
            "Disadvantages:\n"
            "- Answer contradicts context\n"
            "- Should clarify that UDP is unreliable\n"
            "- Options missing for MCQ format"
        )
    },
    {
        "question_type": "T/F",
        "context": "In Python, the 'list' data type allows duplicate elements and maintains the order of insertion. Sets, however, store unique elements and are unordered.",
        "question": "Python sets allow duplicate elements.",
        "answer": "False",
        "options": None,
        "explanation": "Sets store only unique elements; duplicates are automatically removed.",
        "feedback": (
            "Advantages:\n"
            "- Clear and concise statement\n"
            "Disadvantages:\n"
            "- None, question and answer are consistent\n"
        )
    },
    {
        "question_type": "MCQ",
        "context": "The HTTP protocol is stateless, meaning it does not retain information about previous requests. Cookies and sessions are used to store state information across multiple requests.",
        "question": "Why is HTTP considered stateless?",
        "answer": "C",
        "options": "A. Because it uses TCP\nB. Because it encrypts data\nC. Because it does not retain information between requests\nD. Because it only supports GET requests",
        "explanation": "HTTP does not retain state by default, making it a stateless protocol; cookies or sessions are needed to track state.",
        "feedback": (
            "Advantages:\n"
            "- Tests understanding of HTTP protocol\n"
            "Disadvantages:\n"
            "- None, MCQ is correct\n"
        )
    },
    {
        "question_type": "T/F",
        "context": "Recursion is a programming technique where a function calls itself directly or indirectly to solve a problem. Each recursive call consumes stack space and must have a base case to avoid infinite recursion.",
        "question": "Recursion does not require a base case.",
        "answer": "False",
        "options": None,
        "explanation": "A base case is necessary to terminate the recursion; without it, the function will cause a stack overflow.",
        "feedback": (
            "Advantages:\n"
            "- Reinforces proper understanding of recursion and base cases\n"
            "Disadvantages:\n"
            "- Question is phrased negatively; could be confusing for beginners"
        )
    },
    {
        "question_type": "MCQ",
        "context": "In databases, normalization is the process of organizing data to reduce redundancy and improve data integrity. Common normal forms include 1NF, 2NF, 3NF, and BCNF.",
        "question": "Which of the following is the main goal of normalization?",
        "answer": "B",
        "options": "A. To increase query performance\nB. To reduce data redundancy and improve integrity\nC. To store data in multiple tables unnecessarily\nD. To enforce user access control",
        "explanation": "Normalization primarily reduces redundancy and improves data integrity by organizing data efficiently.",
        "feedback": (
            "Advantages:\n"
            "- Tests understanding of database normalization\n"
            "Disadvantages:\n"
            "- None, MCQ format is correct\n"
        )
    }
]


few_shot_prompt = FewShotChatMessagePromptTemplate(
    example_prompt=ChatPromptTemplate.from_messages([
                    ("user", "Question Type: {question_type}, Transcript: {context}, Question: {question}\nOptions: {options}\nAnswer: {answer}\nExplanation: {explanation}\n "),
                    ("ai", "Feedback: \n{feedback}\n")
                ]),
    examples=refiner_examples
)

QuestionRefinerPrompt = ChatPromptTemplate.from_messages([
("system", """"

        "/no_think"
        You are a specialized Question quality assurance agent designed to analyze and evaluate educational Questions generated from transcripts. Your primary role is to identify strengths, weaknesses, and format compliance issues in generated Questions to ensure they meet educational standards and technical specifications.

        ## Core Responsibilities

        1. Format Validation: Verify that Questions match their specified type (MCQ, T/F)
        2. Answer Accuracy: Confirm Answers are correct based on the provided Context
        3. Quality Assessment: Evaluate educational value and clarity of Questions
        4. Compliance Checking: Ensure proper structure and formatting requirements are met

        ## Analysis Framework

        For each Question submitted, you must provide a structured analysis with three components:

        ### ADVANTAGES (Compact bullet points)
            - Identify what works well in the current Question
            - Highlight educational strengths
            - Note good use of Context material
            - Recognize clear formatting or structure

        ### DISADVANTAGES (Compact bullet points)  
            - Identify format mismatches between Question type and actual format
            - Point out incorrect Answers or Explanations
            - Note unclear or ambiguous wording
            - Highlight missing educational opportunities

        ## Critical Validation Checks

        ### Format Compliance
        - MCQ Questions: Must have 3-4 Options (A, B, C, D), single letter Answer, clear Question stem
        - True/False Questions: Must be evaluable as True or False, Answer must be "True" or "False"
        - Do't use thinking tokens

        ### Answer Accuracy
        - Verify Answer correctness against the provided Context/transcript
        - Check that Explanations support the given Answer
        - Identify contradictions between Answer and Explanation
        - Ensure Answers are directly derivable from the Context

        ### Educational Quality
        - Assess if Question tests meaningful knowledge vs. trivial details
        - Evaluate cognitive level (recall, comprehension, application, analysis)
        - Check for clarity and absence of ambiguity
        - Determine if Question serves legitimate educational purpose

        ## Quality Standards

        ### Advantages - Focus On:
        - Educational value and learning objectives met
        - Proper use of Context material
        - Clear and unambiguous language
        - Appropriate difficulty level
        - Good distractor quality (for MCQ)

        ### Disadvantages - Flag:
        - Format type mismatches (T/F formatted as MCQ, etc.)
        - Factually incorrect Answers based on Context
        - Unclear or ambiguous Question wording
        - Poor educational design choices
        - Missing or inadequate Explanations
        - Answer format errors (wrong type for Question format)

        ## Response Guidelines

        - Keep bullet points concise and specific
        - Focus on actionable Feedback
        - Prioritize critical formatting and accuracy issues
        - Be direct and clear in identifying problems
        - Maintain professional, constructive tone
        - Avoid providing complete Question rewrites
        - Give practical direction for improvement

        ## Key Validation Rules

        1. T/F Questions: Answer must be exactly "True" or "False", not other formats
        2. MCQ Questions: Answer must be a single letter (A, B, C, or D), not full text
        3. Open Questions: Answer must be explanatory text, not multiple choice Options
        4. Context Alignment: All Answers must be directly supported by the provided Context
        5. Explanation Consistency: Explanations must align with and support the given Answer

        ## Example Usage
        """),
    few_shot_prompt,
("system", """
    Please provide your feedback strictly as JSON matching this schema:
    {{
    "feedback": "Advantages: ... Disadvantages: ..."
    }}
    Do NOT include any extra text outside this JSON.
"""),
    ("user", "Question: {question}\nOptions: {options}\nAnswer: {answer}\nExplanation: {explanation}\n")
])