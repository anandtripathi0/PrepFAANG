"""Original practice questions. No claim of official company test provenance."""

from sqlalchemy import select

from .admin import QuestionInput, save_question
from .db import SessionLocal
from .models import Company, Pattern, Question, Section, Track

# topic, prompt, choices, correct index, explanation
MCQS = {
    "beginner": [
        (
            "Quantitative Aptitude",
            "A notebook costs ₹80 before a 15% discount. What is the sale price?",
            ["₹65", "₹68", "₹72", "₹75"],
            1,
            "15% of 80 is 12. Subtract 12 from 80 to get ₹68.",
        ),
        (
            "Quantitative Aptitude",
            "A pump fills 120 litres in 8 minutes at a constant rate. How much does it fill in 15 minutes?",
            ["180 litres", "200 litres", "225 litres", "240 litres"],
            2,
            "The rate is 120/8 = 15 litres per minute. In 15 minutes it fills 225 litres.",
        ),
        (
            "Logical Reasoning",
            "All gliders are aircraft. Some aircraft are electric. Which conclusion must follow?",
            [
                "All gliders are electric",
                "Some gliders are electric",
                "No gliders are electric",
                "None of the first three conclusions is guaranteed",
            ],
            3,
            "The electric aircraft may or may not include gliders.",
        ),
        (
            "Logical Reasoning",
            "A sequence starts 4, 9, 14, 19. If the difference stays constant, what is the sixth term?",
            ["24", "25", "29", "30"],
            2,
            "Add 5 at each step. The fifth term is 24 and the sixth is 29.",
        ),
        (
            "Verbal Ability",
            "Choose the sentence with correct subject–verb agreement.",
            [
                "The list of items are ready.",
                "The list of items is ready.",
                "The lists of item is ready.",
                "The list have been ready.",
            ],
            1,
            "The singular subject “list” takes “is”; “of items” does not change the subject.",
        ),
        (
            "Verbal Ability",
            "A report describes a result as tentative. What does tentative mean here?",
            ["Certain and final", "Provisional and subject to change", "Unrelated", "Impossible"],
            1,
            "A tentative result is provisional until further evidence confirms it.",
        ),
        (
            "Programming Fundamentals",
            "What is the final value of x after x = 3, then x = x * 2 + 1?",
            ["6", "7", "8", "9"],
            1,
            "Multiplication happens before addition: 3 × 2 + 1 = 7.",
        ),
        (
            "DBMS",
            "Which property makes a primary key suitable for identifying each row?",
            ["It can contain duplicates", "It is always text", "It is unique and not null", "It must change each day"],
            2,
            "A primary key uniquely identifies a row and does not permit null values.",
        ),
        (
            "Operating Systems",
            "What is the main role of an operating system scheduler?",
            [
                "Choose which ready process runs next",
                "Encrypt every file",
                "Compile programs",
                "Design database tables",
            ],
            0,
            "A scheduler assigns processor time to ready processes.",
        ),
        (
            "Computer Networks",
            "Which service maps a domain name to an IP address?",
            ["DNS", "FTP", "SSH", "NTP"],
            0,
            "DNS resolves names to records, including IP address records.",
        ),
        (
            "Data Interpretation",
            "A store sold 12, 18 and 30 units on three days. What fraction of the total was sold on day three?",
            ["1/4", "1/3", "1/2", "2/3"],
            2,
            "The total is 60. Day three accounts for 30/60 = 1/2.",
        ),
        (
            "OOP",
            "Which concept groups data and the operations on that data behind an interface?",
            ["Encapsulation", "Sorting", "Recursion", "Scheduling"],
            0,
            "Encapsulation packages state and behavior and controls access to them.",
        ),
        (
            "SQL",
            "Which clause filters individual rows before aggregation?",
            ["ORDER BY", "HAVING", "WHERE", "LIMIT"],
            2,
            "WHERE filters source rows; HAVING filters groups after aggregation.",
        ),
        (
            "Cloud Fundamentals",
            "Which resource is typically provided by infrastructure as a service?",
            ["A virtual machine", "Only an email inbox", "A handwritten report", "A physical employee"],
            0,
            "IaaS exposes computing infrastructure such as virtual machines, networks and storage.",
        ),
        (
            "Cybersecurity Fundamentals",
            "Why should passwords be stored with a salted password hash?",
            [
                "To recover the original password",
                "To slow offline guessing and prevent equal passwords having equal stored hashes",
                "To make passwords public",
                "To avoid authentication",
            ],
            1,
            "Salts prevent shared precomputed lookup attacks, while password hash work factors slow guessing.",
        ),
        (
            "DSA",
            "What is the lookup time for an array element by a valid index?",
            ["O(1)", "O(log n)", "O(n)", "O(n²)"],
            0,
            "Contiguous fixed-size elements allow direct address calculation.",
        ),
        (
            "Computer Fundamentals",
            "How many distinct values can an unsigned 8-bit integer represent?",
            ["8", "128", "255", "256"],
            3,
            "Eight independent bits yield 2^8 = 256 values, from 0 through 255.",
        ),
    ],
    "moderate": [
        (
            "Quantitative Aptitude",
            "A can finish a job in 12 days and B in 18 days. Working together at constant rates, how long do they take?",
            ["6 days", "7.2 days", "9 days", "15 days"],
            1,
            "Their combined rate is 1/12 + 1/18 = 5/36 jobs per day, so time is 36/5 days.",
        ),
        (
            "Quantitative Aptitude",
            "A bag has 4 blue and 6 red tokens. Two are drawn without replacement. What is the probability that both are blue?",
            ["2/15", "4/25", "1/5", "3/10"],
            0,
            "Multiply 4/10 by 3/9 to obtain 12/90 = 2/15.",
        ),
        (
            "Logical Reasoning",
            "Five tasks have dependencies A before C, B before C, C before D, and B before E. Which order is valid?",
            ["A C B D E", "B E A C D", "C A B E D", "A B D C E"],
            1,
            "B E A C D satisfies every dependency; each other sequence violates at least one.",
        ),
        (
            "Logical Reasoning",
            "Exactly one of P and Q is true. If P implies R and R is false, what must be true?",
            ["P is true", "Q is true", "Both are false", "R is true"],
            1,
            "A true implication P → R and false R imply false P. Exactly one of P and Q then forces Q true.",
        ),
        (
            "Verbal Ability",
            "A pilot programme increased attendance, but participants volunteered. Which limitation most directly weakens a causal claim?",
            [
                "Attendance can be measured",
                "Volunteers may already be more motivated",
                "The programme has a name",
                "The report contains a chart",
            ],
            1,
            "Self-selection may explain attendance differences independently of the programme.",
        ),
        (
            "Verbal Ability",
            "Choose the clearest sentence without a dangling modifier.",
            [
                "After reviewing the logs, the bug was clear.",
                "After reviewing the logs, Mira identified the bug.",
                "Reviewing the logs, the bug appeared.",
                "The bug, after reviewing logs, was fixed.",
            ],
            1,
            "Mira is explicitly the person reviewing the logs and identifying the bug.",
        ),
        (
            "Programming Fundamentals",
            "A function appends to a mutable list passed as an argument. What can happen to the caller’s list?",
            [
                "It can change because both references point to the same list",
                "It must remain unchanged",
                "It becomes immutable",
                "It is always deleted",
            ],
            0,
            "Sharing a reference to a mutable object allows the callee to mutate that object.",
        ),
        (
            "DBMS",
            "Two transactions read the same balance and independently overwrite it after adding a deposit. Which anomaly can occur?",
            ["Lost update", "Perfect serialization", "Automatic normalization", "Index fragmentation only"],
            0,
            "One write may overwrite the other, losing one deposit unless concurrency is controlled.",
        ),
        (
            "Operating Systems",
            "A process holds a lock while waiting for another lock held by a waiting process. Which condition is present?",
            ["Circular wait", "No mutual exclusion", "No hold-and-wait", "Guaranteed progress"],
            0,
            "A cycle of processes waiting for locks held by each other is circular wait.",
        ),
        (
            "Computer Networks",
            "Why can a TCP receiver acknowledge data that arrived in several segments with one cumulative acknowledgement?",
            [
                "TCP numbers bytes in an ordered stream",
                "TCP never loses packets",
                "TCP uses only one packet",
                "TCP omits sequencing",
            ],
            0,
            "The acknowledgement identifies the next expected byte and cumulatively acknowledges earlier bytes.",
        ),
        (
            "Data Interpretation",
            "A product’s revenue rises 20% while units sold rise 50%. What happens to average revenue per unit?",
            ["Rises 30%", "Falls 20%", "Falls 30%", "Stays constant"],
            1,
            "Revenue per unit changes by 1.2/1.5 = 0.8, a 20% decrease.",
        ),
        (
            "OOP",
            "A function accepts a base-type object and calls an overridden method. What determines the implementation under dynamic dispatch?",
            ["The runtime object type", "The variable name", "The source file size", "Alphabetical method order"],
            0,
            "Dynamic dispatch chooses the override associated with the runtime object.",
        ),
        (
            "SQL",
            "A LEFT JOIN from customers to orders is followed by WHERE orders.status = paid. What happens to customers without orders?",
            ["They are excluded", "They appear twice", "They always remain", "Their IDs become paid"],
            0,
            "Their joined status is null; the WHERE equality predicate does not evaluate to true.",
        ),
        (
            "Cloud Fundamentals",
            "A stateless service has uneven request volume. Which strategy adds capacity as demand grows?",
            [
                "Horizontal autoscaling",
                "Hardcoding one server",
                "Removing all metrics",
                "Storing sessions only in process memory",
            ],
            0,
            "Horizontal autoscaling changes the number of service instances in response to load signals.",
        ),
        (
            "Cybersecurity Fundamentals",
            "What most directly prevents a user from accessing another user’s record by changing its URL identifier?",
            ["Server-side ownership checks", "Hiding the link", "A longer CSS class name", "Disabling right click"],
            0,
            "Every record request must enforce authorization on the server using the authenticated user.",
        ),
        (
            "DSA",
            "Which algorithm finds shortest paths from one source in an unweighted graph?",
            ["Breadth-first search", "Any depth-first search", "Selection sort", "Binary search"],
            0,
            "BFS explores increasing numbers of edges from the source.",
        ),
        (
            "Computer Fundamentals",
            "A cache uses 64-byte lines. How many line-offset bits are needed?",
            ["4", "5", "6", "8"],
            2,
            "Six bits address 2^6 = 64 bytes within a cache line.",
        ),
    ],
    "pro": [
        (
            "Quantitative Aptitude",
            "A fair die is rolled until a 6 appears. What is the expected number of rolls, including the final roll?",
            ["3", "3.5", "5", "6"],
            3,
            "For geometric success probability p = 1/6, the expected number of trials is 1/p = 6.",
        ),
        (
            "Quantitative Aptitude",
            "How many length-5 binary strings contain no two adjacent 1s?",
            ["10", "12", "13", "16"],
            2,
            "Let f(n)=f(n−1)+f(n−2), with f(1)=2 and f(2)=3. Then f(5)=13.",
        ),
        (
            "Logical Reasoning",
            "Exactly two of A, B, C are true. A implies not B, and C implies A. Which assignment works?",
            ["A and B true", "A and C true", "B and C true", "None works"],
            1,
            "A and C true with B false satisfies both implications. The other pairs violate one.",
        ),
        (
            "Logical Reasoning",
            "There are 9 identical-looking coins; exactly one is heavier. What is the minimum worst-case number of balance-scale weighings needed?",
            ["1", "2", "3", "4"],
            1,
            "Weigh groups of three to locate the heavy group, then compare two coins from that group.",
        ),
        (
            "Verbal Ability",
            "A model predicts well on historical data but fails after a policy change. Which inference is best supported?",
            [
                "The historical relationships may not generalize after the change",
                "The model never fit historical data",
                "All prediction is impossible",
                "The policy had no effect",
            ],
            0,
            "A distribution shift can invalidate relationships learned from past data.",
        ),
        (
            "Verbal Ability",
            "Which revision preserves the scope of “Not all applicants who passed coding passed aptitude”?",
            [
                "No applicants passed aptitude",
                "At least one coding-pass applicant did not pass aptitude",
                "All coding-pass applicants failed aptitude",
                "Every applicant failed coding",
            ],
            1,
            "Negating a universal claim implies at least one counterexample, not that every case fails.",
        ),
        (
            "Programming Fundamentals",
            "A closure captures a mutable variable by reference. The variable changes before the closure runs. Which value is generally read?",
            ["Its value when the closure runs", "Always the original value", "Always zero", "No value is possible"],
            0,
            "Reference capture resolves through the captured storage, whose contents may change.",
        ),
        (
            "DBMS",
            "Two transactions each check that another doctor is on call, then turn themselves off call. Snapshot isolation can allow which anomaly?",
            ["Write skew", "A guaranteed serialization failure", "A dirty read by definition", "A syntax error"],
            0,
            "Transactions update different rows after reading a shared invariant, so both can commit and violate it.",
        ),
        (
            "Operating Systems",
            "A low-priority task owns a mutex needed by a high-priority task while medium-priority tasks keep running. Which technique mitigates the problem?",
            ["Priority inheritance", "Disabling all locks", "Increasing page size", "FIFO disk scheduling"],
            0,
            "Priority inheritance temporarily raises the lock owner’s scheduling priority.",
        ),
        (
            "Computer Networks",
            "An HTTP client retries a payment request after a timeout. What allows safe retries without duplicate charges?",
            ["A server-enforced idempotency key", "A shorter URL", "Disabling TLS", "Changing the button color"],
            0,
            "A persisted idempotency key maps retries of one logical operation to one result.",
        ),
        (
            "Data Interpretation",
            "Group A improves from 8/10 to 18/20 successes. Group B improves from 1/10 to 16/80. Why does the combined rate fall?",
            [
                "The later sample is weighted more heavily toward the lower-performing group",
                "Both group rates actually fall",
                "Percentages cannot be aggregated",
                "The arithmetic must be wrong",
            ],
            0,
            "The mix shifts: initially 9/20=45%; later 34/100=34%, despite within-group improvement.",
        ),
        (
            "OOP",
            "A subtype rejects inputs accepted by its base type’s contract. Which principle is most directly violated?",
            ["Liskov substitution", "Binary search", "Cache locality", "Eventual consistency"],
            0,
            "A usable subtype must not strengthen preconditions in a way that breaks valid base-type clients.",
        ),
        (
            "SQL",
            "For amounts 10, 10, 20 ordered ascending, what ranks does DENSE_RANK produce?",
            ["1, 1, 2", "1, 2, 3", "1, 1, 3", "0, 1, 2"],
            0,
            "DENSE_RANK assigns equal ranks to peers and does not leave gaps.",
        ),
        (
            "Cloud Fundamentals",
            "During a network partition, a strongly consistent quorum-based store may reject some writes. Which trade-off does this demonstrate?",
            [
                "Consistency can require reduced availability during partitions",
                "Partitions improve all guarantees",
                "Replication removes latency",
                "Durability and authentication are identical",
            ],
            0,
            "A partition can prevent a quorum; rejecting operations preserves consistency at the cost of availability.",
        ),
        (
            "Cybersecurity Fundamentals",
            "Why is checking only a file extension insufficient before processing an upload?",
            [
                "The extension can disagree with content and parser behavior",
                "Extensions are always encrypted",
                "All file content is safe",
                "Extensions determine permissions universally",
            ],
            0,
            "Validate content, size, supported formats and processing isolation; a name is not trustworthy evidence.",
        ),
        (
            "DSA",
            "What invariant supports binary search for the first true value of a predicate over sorted positions?",
            [
                "The predicate is false then true with at most one transition",
                "Every value is unique",
                "The array length is prime",
                "The predicate alternates each position",
            ],
            0,
            "A monotone predicate allows discarding half the search interval while preserving the boundary.",
        ),
        (
            "Computer Fundamentals",
            "Why can two threads updating different variables in one cache line still interfere with performance?",
            [
                "False sharing causes coherence traffic",
                "The variables must be equal",
                "The compiler cannot generate stores",
                "Virtual memory is unavailable",
            ],
            0,
            "Cache coherence tracks whole lines, so independent writes may repeatedly invalidate the same line.",
        ),
    ],
}

STARTERS = {
    "python": "import sys\n\ndef solve():\n    data = sys.stdin.read().split()\n    # Write your solution here\n\nsolve()\n",
    "javascript": "const fs = require('fs');\nconst data = fs.readFileSync(0, 'utf8').trim().split(/\\s+/);\n// Write your solution here\n",
    "c": "#include <stdio.h>\nint main(void) {\n    /* Write your solution here */\n    return 0;\n}\n",
    "cpp": "#include <iostream>\n#include <vector>\nusing namespace std;\nint main() {\n    // Write your solution here\n}\n",
    "java": "import java.util.*;\npublic class Main {\n    public static void main(String[] args) {\n        Scanner in = new Scanner(System.in);\n        // Write your solution here\n    }\n}\n",
}

CODING = [
    (
        "array-total",
        "Array total",
        "beginner",
        "Given n integers, print their sum.",
        "n followed by n space-separated integers.",
        "One integer: the sum.",
        "1 ≤ n ≤ 10000; −1000000 ≤ a[i] ≤ 1000000.",
        [
            ("4\n2 -1 5 3\n", "9\n", False),
            ("1\n0\n", "0\n", True),
            ("3\n-3 -2 -1\n", "-6\n", True),
            ("2\n1000000 1000000\n", "2000000\n", True),
        ],
        "Accumulate the numbers in a variable wide enough for the sum.",
    ),
    (
        "word-mirror",
        "Word mirror",
        "beginner",
        "Reverse a nonempty lowercase word and print the result.",
        "A single lowercase word.",
        "The reversed word.",
        "1 ≤ length ≤ 10000.",
        [
            ("forge\n", "egrof\n", False),
            ("a\n", "a\n", True),
            ("level\n", "level\n", True),
            ("abcde\n", "edcba\n", True),
        ],
        "Read the word and traverse its characters from right to left.",
    ),
    (
        "target-pairs",
        "Target pairs",
        "moderate",
        "Count pairs of indices i < j whose values add to target. Count equal-valued elements at different indices separately.",
        "n and target on the first line; n integers on the second.",
        "The number of valid index pairs.",
        "1 ≤ n ≤ 100000; |a[i]|, |target| ≤ 1000000000.",
        [
            ("5 6\n1 5 3 3 2\n", "2\n", False),
            ("4 4\n2 2 2 2\n", "6\n", True),
            ("3 0\n-1 0 1\n", "1\n", True),
            ("1 2\n1\n", "0\n", True),
        ],
        "Maintain frequencies of previously seen values. Add the frequency of target−x before inserting x.",
    ),
    (
        "longest-distinct",
        "Longest distinct window",
        "moderate",
        "Find the length of the longest contiguous substring whose characters are all different.",
        "One nonempty lowercase word.",
        "Length of the longest distinct-character substring.",
        "1 ≤ length ≤ 100000.",
        [("abcaef\n", "5\n", False), ("aaaa\n", "1\n", True), ("abcabcbb\n", "3\n", True), ("pwwkew\n", "3\n", True)],
        "Use a sliding window and each character’s last position to advance the left boundary.",
    ),
    (
        "minimum-coins",
        "Minimum coins",
        "pro",
        "Given coin denominations and a target, print the fewest coins needed to make the target, using each denomination any number of times. Print -1 if impossible.",
        "n and target, followed by n positive denominations.",
        "Minimum count, or -1.",
        "1 ≤ n ≤ 100; 0 ≤ target ≤ 10000; 1 ≤ denomination ≤ 10000.",
        [
            ("3 6\n1 3 4\n", "2\n", False),
            ("2 7\n2 4\n", "-1\n", True),
            ("2 0\n2 5\n", "0\n", True),
            ("3 11\n1 5 7\n", "3\n", True),
        ],
        "Let dp[x] be the minimum count to form x; consider dp[x−coin]+1 for each usable coin.",
    ),
    (
        "shortest-route",
        "Shortest unweighted route",
        "pro",
        "In an undirected graph, return the fewest edges from vertex 1 to vertex n, or -1 if unreachable.",
        "n m, followed by m lines containing endpoints u v.",
        "The shortest distance from 1 to n.",
        "1 ≤ n ≤ 100000; 0 ≤ m ≤ 200000.",
        [
            ("4 4\n1 2\n2 4\n1 3\n3 4\n", "2\n", False),
            ("3 1\n1 2\n", "-1\n", True),
            ("1 0\n", "0\n", True),
            ("4 3\n1 2\n2 3\n3 4\n", "3\n", True),
        ],
        "Use breadth-first search, marking each vertex when first enqueued.",
    ),
]


def seed():
    with SessionLocal() as db:
        for difficulty, questions in MCQS.items():
            for i, (topic, prompt, options, correct, explanation) in enumerate(questions):
                slug = f"{difficulty}-{i + 1}"
                if not db.scalar(select(Question).where(Question.slug == slug)):
                    save_question(
                        db,
                        QuestionInput(
                            slug=slug,
                            title=prompt,
                            question=prompt,
                            options=options,
                            correct_answer=correct,
                            explanation=explanation,
                            difficulty=difficulty,
                            topic=topic,
                        ),
                    )
                    db.commit()
        for slug, title, difficulty, prompt, input_fmt, output_fmt, constraints, tests, explanation in CODING:
            if not db.scalar(select(Question).where(Question.slug == slug)):
                save_question(
                    db,
                    QuestionInput(
                        slug=slug,
                        type="coding",
                        title=title,
                        question=prompt,
                        explanation=explanation,
                        difficulty=difficulty,
                        topic="Coding",
                        tags=[
                            "Arrays"
                            if slug in ("array-total", "target-pairs")
                            else "Strings"
                            if slug in ("word-mirror", "longest-distinct")
                            else "Dynamic Programming"
                            if slug == "minimum-coins"
                            else "Graphs"
                        ],
                        coding={
                            "input_format": input_fmt,
                            "output_format": output_fmt,
                            "constraints": constraints,
                            "starter_code": STARTERS,
                            "allowed_languages": list(STARTERS),
                            "tests": [{"input": a, "output": b, "hidden": c} for a, b, c in tests],
                        },
                    ),
                )
                db.commit()
        groups = {
            "Big Tech": ["Google", "Amazon", "Microsoft", "Meta", "Apple"],
            "IT Services": ["TCS", "Infosys", "Wipro", "Accenture", "Cognizant", "Capgemini"],
            "Consulting": ["Deloitte"],
            "Product Companies": ["IBM", "Oracle", "Adobe"],
        }
        for category, names in groups.items():
            for name in names:
                slug = name.lower()
                if db.scalar(select(Company).where(Company.slug == slug)):
                    continue
                company = Company(
                    name=name,
                    slug=slug,
                    category=category,
                    description=f"Build your foundations for {name}-focused preparation with original aptitude, technical and coding practice. These configurations are independently created, not official or verified current hiring patterns.",
                )
                db.add(company)
                db.flush()
                track_names = (
                    ["Graduate Engineer", "Software Engineer"]
                    if category == "IT Services"
                    else ["Software Engineer", "Internship"]
                )
                for track_name in track_names:
                    track = Track(company_id=company.id, name=track_name)
                    db.add(track)
                    db.flush()
                    pattern = Pattern(track_id=track.id, duration_minutes=30)
                    db.add(pattern)
                    db.flush()
                    for position, (section_name, topics, count, marks) in enumerate(
                        [
                            ("Aptitude", ["Quantitative Aptitude"], 2, 2),
                            ("Reasoning", ["Logical Reasoning"], 2, 2),
                            ("Verbal", ["Verbal Ability"], 1, 2),
                            (
                                "Technical",
                                ["DBMS", "Operating Systems", "Programming Fundamentals", "DSA", "SQL"],
                                2,
                                2,
                            ),
                            ("Coding", ["Coding"], 1, 6),
                        ]
                    ):
                        db.add(
                            Section(
                                pattern_id=pattern.id,
                                name=section_name,
                                topics=topics,
                                question_count=count,
                                marks=marks,
                                negative_marks=0,
                                position=position,
                            )
                        )
                db.commit()
        db.commit()
        from .mixed_bank import seed_mixed

        seed_mixed(db)
        print(
            "Seed complete: 15 companies, 30 tracks, 231 original MCQs, 15 reflection items and 6 coding problems. Safe to rerun."
        )


if __name__ == "__main__":
    seed()
