"""Original educational content authored for PrepFaang. No third-party questions.

Quantitative families use checked arithmetic; each family teaches a distinct
concept. Difficulty variants change inputs or reasoning depth. Psychometric
items are unscored work-style reflections, not a validated psychological test.
"""

import random
from fractions import Fraction
from math import comb, gcd

TOPICS = [
    "Quantitative Aptitude",
    "Logical Reasoning",
    "Verbal Ability",
    "Data Interpretation",
    "Psychometric Reflection",
]
LEVELS = ["beginner", "moderate", "pro"]


def item(level, topic, subtopic, prompt, correct, alternatives, explanation):
    options = list(dict.fromkeys(map(str, [correct, *alternatives])))
    if len(options) != 4:
        raise ValueError(f"Question needs four distinct options: {topic}/{subtopic}/{level}")
    slug = "pf-" + level + "-" + topic.split()[0].lower() + "-" + subtopic.lower().replace(" ", "-")
    random.Random(slug).shuffle(options)
    return dict(
        slug=slug,
        type="mcq",
        title=subtopic,
        question=prompt,
        options=options,
        correct_answer=options.index(str(correct)),
        explanation=explanation,
        difficulty=level,
        topic=topic,
        subtopic=subtopic,
        tags=["original", "mixed-set"],
        estimated_time=90,
    )


def numeric(level, topic, title, prompt, answer, explanation):
    answer = Fraction(answer)
    step = max(1, abs(answer.numerator) // max(1, answer.denominator) // 5)
    return item(
        level,
        topic,
        title,
        prompt,
        str(answer),
        [str(answer + step), str(answer - step), str(answer + 2 * step)],
        explanation,
    )


def quant(level, k):
    t = TOPICS[0]
    p = 400 + 200 * k
    rate = 10 + 5 * k
    yield numeric(
        level,
        t,
        "Percentage increase",
        f"A workshop has {p} bookings. Bookings increase by {rate}%. How many bookings are there now?",
        p * (100 + rate) // 100,
        f"New bookings = {p} × (1 + {rate}/100) = {p * (100 + rate) // 100}.",
    )
    cost = 600 + 200 * k
    profit = 15 + 5 * k
    yield numeric(
        level,
        t,
        "Profit on cost",
        f"A component costs ₹{cost}. It is sold at a {profit}% profit on cost. What is the selling price in rupees?",
        cost * (100 + profit) // 100,
        "Profit is calculated on cost. Multiply cost by (100 + profit percentage)/100.",
    )
    total = 84 + 42 * k
    yield numeric(
        level,
        t,
        "Ratio allocation",
        f"A lab divides {total} sensors between teams in the ratio 2:5. How many sensors does the larger team get?",
        total * 5 // 7,
        f"There are seven ratio parts; the larger team gets 5 × {total}/7.",
    )
    average = 18 + 3 * k
    extra = 30 + 5 * k
    yield numeric(
        level,
        t,
        "Updated average",
        f"Five readings have mean {average}. A sixth reading is {extra}. What is the new mean?",
        Fraction(5 * average + extra, 6),
        "Recover the original total as 5 × mean, add the sixth reading, then divide by 6.",
    )
    a = 12 + 6 * k
    b = 2 * a
    yield numeric(
        level,
        t,
        "Combined work",
        f"Machine A completes an order in {a} hours and B in {b} hours. At constant rates, how many hours do they need together?",
        Fraction(a * b, a + b),
        "Add work rates: 1/A + 1/B. The completion time is AB/(A+B).",
    )
    speed = 30 + 10 * k
    distance = 2 * speed * (3 + k)
    yield numeric(
        level,
        t,
        "Round trip speed",
        f"A courier travels {distance} km at {speed} km/h and returns the same distance at {2 * speed} km/h. What is the average speed for the whole trip in km/h?",
        Fraction(4 * speed, 3),
        "Average speed is total distance divided by total time, not the arithmetic mean of the speeds.",
    )
    principal = 2000 + 1000 * k
    years = k + 2
    yield numeric(
        level,
        t,
        "Simple interest",
        f"₹{principal} earns simple interest at 6% per year for {years} years. What is the interest in rupees?",
        principal * 6 * years // 100,
        "Simple interest = principal × annual rate × years / 100.",
    )
    amount = 1000 + 500 * k
    yield numeric(
        level,
        t,
        "Successive growth",
        f"An account starts at ₹{amount} and grows by 10% in each of two periods. What is its value after the second period?",
        Fraction(amount * 121, 100),
        "Each period multiplies the current balance by 1.10; use the compound factor 1.21.",
    )
    red = 3 + k
    blue = 5 + 2 * k
    yield numeric(
        level,
        t,
        "Without replacement",
        f"A box has {red} red and {blue} blue tiles. Two tiles are drawn without replacement. What is the probability both are red?",
        Fraction(red * (red - 1), (red + blue) * (red + blue - 1)),
        "Multiply red/total by (red−1)/(total−1). The second draw has a smaller sample space.",
    )
    people = 6 + k
    yield numeric(
        level,
        t,
        "Committee selection",
        f"A group of {people} volunteers selects a committee of three, with no distinct roles. How many committees are possible?",
        comb(people, 3),
        "Order does not matter. Use n choose 3 = n(n−1)(n−2)/6.",
    )
    x = 18 + 6 * k
    y = 24 + 8 * k
    yield numeric(
        level,
        t,
        "Repeating schedules",
        f"One signal flashes every {x} seconds and another every {y} seconds. Both flash now. After how many seconds will they next flash together?",
        x * y // gcd(x, y),
        "Find the least common multiple: LCM(a,b) = ab/GCD(a,b).",
    )
    first = 4 + k
    diff = 3 + k
    n = 10 + 5 * k
    yield numeric(
        level,
        t,
        "Arithmetic series",
        f"An arithmetic sequence has first term {first}, common difference {diff}, and {n} terms. What is the sum?",
        Fraction(n * (2 * first + (n - 1) * diff), 2),
        "The last term is a+(n−1)d. Sum = n × (first + last)/2.",
    )
    low = 20 + 5 * k
    high = 60 + 5 * k
    yield numeric(
        level,
        t,
        "Mixture concentration",
        f"Equal volumes of {low}% and {high}% solutions are mixed. Then an equal volume of pure water is added to that mixture. What is the final concentration as a numerical percentage?",
        Fraction(low + high, 4),
        "Equal-volume mixing first gives the average concentration. Adding the same volume of water halves it.",
    )
    width = 8 + 2 * k
    length = width + 5
    yield numeric(
        level,
        t,
        "Border area",
        f"A rectangular board is {length} m long and {width} m wide. A 1 m border is painted inside all four edges. What area is painted in square metres?",
        length * width - (length - 2) * (width - 2),
        "Subtract the unpainted inner rectangle, whose length and width are each reduced by 2 m.",
    )
    n = 3 + k
    yield numeric(
        level,
        t,
        "Algebraic substitution",
        f"If x + y = {4 * n} and x − y = {2 * n}, what is xy?",
        3 * n * n,
        "Add the equations to find x, subtract to find y, then multiply. Here x=3n and y=n.",
    )


def logical(level, k):
    t = TOPICS[1]
    n = k + 2
    records = [
        (
            "Increasing differences",
            f"Continue the sequence: {n}, {n + 2}, {n + 6}, {n + 12}, {n + 20}, ?",
            n + 30,
            [n + 28, n + 32, n + 26],
            "Successive differences are 2,4,6,8,10.",
        ),
        (
            "Alternating operations",
            f"Start at {n}. Repeatedly multiply by 3, then subtract 2. What is the value after four operations?",
            9 * n - 8,
            [9 * n - 6, 9 * n - 2, 3 * n - 4],
            "The four values are 3n, 3n−2, 9n−6, and 9n−8.",
        ),
        (
            "Queue position",
            f"A person is {8 + k}th from the front and {11 + k}th from the back of a queue. How many people are in it?",
            18 + 2 * k,
            [19 + 2 * k, 17 + 2 * k, 20 + 2 * k],
            "Add both ranks and subtract one because the person was counted twice.",
        ),
        (
            "Direction tracking",
            f"A robot moves {5 + n} m east, {3 + n} m north, {2 + n} m west, then {3 + n} m south. Where is it relative to the start?",
            "3 m east",
            ["3 m west", f"{5 + n} m north", "At the start"],
            "North/south movements cancel. Net eastward displacement is (5+n)−(2+n)=3.",
        ),
        (
            "Set intersection",
            f"In a group of {40 + 10 * k}, {24 + 5 * k} study Python and {20 + 5 * k} study SQL. Everyone studies at least one. How many study both?",
            4,
            [0, 8, 10],
            "Use inclusion–exclusion: both = Python + SQL − total.",
        ),
        (
            "Pigeonhole guarantee",
            f"Tokens come in {3 + k} colours. What is the smallest number of tokens that guarantees at least three of one colour?",
            2 * (3 + k) + 1,
            [2 * (3 + k), 3 * (3 + k), 3 + k + 1],
            "You can take two of each colour without a triple. The next token forces one.",
        ),
        (
            "Letter shift",
            f"Shift each letter of CODE forward by {k + 1} places without changing order. Which result follows?",
            "".join(chr(ord(c) + k + 1) for c in "CODE"),
            ["CODE", "DPEF", "EPFG"] if k != 0 else ["CODE", "EPFG", "FQGH"],
            "Apply the same forward alphabet shift separately to every letter.",
        ),
        (
            "Task dependencies",
            "Jobs require A before C, B before C, C before D, and D before E. Which schedule satisfies all rules?",
            "B A C D E",
            ["A C B D E", "A B D C E", "A B C E D"],
            "Both A and B precede C; C precedes D; D precedes E.",
        ),
        (
            "Necessary conclusion",
            "All authenticated requests have a valid session. This request has no valid session. What follows?",
            "It is not authenticated",
            ["It is authenticated", "Every valid session is this request", "No request can be authenticated"],
            "Contraposition of authenticated → valid session gives no valid session → not authenticated.",
        ),
        (
            "Possibility versus certainty",
            "Some designers are mentors. Every mentor is trained. Which statement must be true?",
            "Some designers are trained",
            ["All designers are trained", "All trained people are designers", "No designers are trained"],
            "The designers known to be mentors inherit the trained property.",
        ),
        (
            "Relative order",
            "Nia finishes before Omar. Pia finishes after Omar but before Rui. Who must finish first among these four?",
            "Nia",
            ["Omar", "Pia", "Rui"],
            "The constraints imply Nia < Omar < Pia < Rui.",
        ),
        (
            "Exclusive conditions",
            "Exactly one of two alarms A and B is active. A is inactive. What must follow?",
            "B is active",
            ["B is inactive", "Both are active", "Neither is active"],
            "An exclusive choice with A false forces B true.",
        ),
        (
            "Calendar offset",
            f"An event occurs on Monday. Another occurs {10 + 7 * k} days later. On which weekday is the second event?",
            "Thursday",
            ["Wednesday", "Friday", "Sunday"],
            "10+7k leaves remainder 3 when divided by 7. Three days after Monday is Thursday.",
        ),
        (
            "Balanced comparisons",
            "Five distinct scores satisfy A > B > C and C > D > E. Which score is the median?",
            "C",
            ["A", "B", "D"],
            "The complete ordering is A>B>C>D>E; C is the third of five.",
        ),
        (
            "Constraint counting",
            f"A code consists of two different digits selected from 1 through {5 + k}. Order matters. How many codes are possible?",
            (5 + k) * (4 + k),
            [(5 + k) ** 2, comb(5 + k, 2), 5 + k],
            "There are n choices for the first digit and n−1 for the second.",
        ),
    ]
    # Shift distractors must remain distinct for each variant.
    records[6] = (records[6][0], records[6][1], records[6][2], ["CODE", "ZABC", "BCDE"], records[6][4])
    for title, prompt, correct, wrong, explanation in records:
        yield item(level, t, title, prompt, correct, wrong, explanation)


def interpretation(level, k):
    t = TOPICS[3]
    f = k + 1
    # Independent datasets per concept, with all units and denominators explicit.
    cases = [
        (
            "Table total",
            f"Orders by depot: North {12 * f}, East {18 * f}, West {25 * f}. How many orders were received altogether?",
            55 * f,
            "Add the three depot counts.",
        ),
        (
            "Share of total",
            f"Tickets by channel: Web {30 * f}, App {50 * f}, Phone {20 * f}. What percentage of all tickets came through the app?",
            50,
            "App / all channels × 100 = 50/100 × 100.",
        ),
        (
            "Percentage growth",
            f"Revenue was ₹{80 * f} thousand in April and ₹{100 * f} thousand in May. What was the percentage increase?",
            25,
            "The increase is 20f on an original base of 80f: 20/80 × 100.",
        ),
        (
            "Weighted average",
            f"Group A has {10 * f} learners averaging 60 marks. Group B has {20 * f} learners averaging 75 marks. What is the combined average?",
            70,
            "Total marks / learners = (10×60+20×75)/30 = 70.",
        ),
        (
            "Percentage points",
            f"A survey records support at {35 + 5 * k}% in round one and {47 + 5 * k}% in round two. By how many percentage points did support change?",
            12,
            "Subtract percentages directly when asked for percentage points.",
        ),
        (
            "Missing observation",
            f"Five days have an average of {20 * f} deliveries. Four daily counts are {12 * f}, {18 * f}, {21 * f}, {24 * f}. Find the fifth count.",
            25 * f,
            "Required total is 100f. Known counts add to 75f, leaving 25f.",
        ),
        (
            "Ratio from data",
            f"A chart gives {45 * f} online and {30 * f} offline registrations. What is online divided by offline, as a simplified fraction?",
            Fraction(3, 2),
            "45f/30f simplifies to 3/2.",
        ),
        (
            "Capacity utilization",
            f"A plant can make {500 * f} units each week. It made {375 * f}. What percentage of capacity was used?",
            75,
            "Actual output / capacity × 100 = 375/500 × 100.",
        ),
        (
            "Overall defect rate",
            f"Line A makes {200 * f} parts with a 5% defect rate. Line B makes {300 * f} parts with a 2% defect rate. What is the overall numerical defect percentage?",
            Fraction(16, 5),
            "Defects are 10f+6f=16f out of 500f parts. The percentage is 3.2 = 16/5.",
        ),
        (
            "Pie chart angle",
            f"A budget assigns {25 + 5 * k}% to research. How many degrees should this occupy in a 360-degree pie chart?",
            Fraction((25 + 5 * k) * 360, 100),
            "Multiply the percentage as a fraction by 360 degrees.",
        ),
        (
            "Median from records",
            f"Daily wait times in minutes are {3 * f}, {8 * f}, {4 * f}, {9 * f}, {6 * f}. What is the median?",
            6 * f,
            "Sort the five observations. The middle one is 6f.",
        ),
        (
            "Range from records",
            f"Measured lengths are {14 * f}, {19 * f}, {11 * f}, {17 * f} cm. What is their range in cm?",
            8 * f,
            "Range is largest minus smallest: 19f−11f.",
        ),
        (
            "Unit conversion",
            f"A dashboard reports transfers of {2 * f} GB, {1500 * f} MB and {500 * f} MB. Using 1 GB = 1000 MB, what is the total in GB?",
            4 * f,
            "The latter two quantities total 2000f MB = 2f GB; add the first 2f GB.",
        ),
        (
            "Net change",
            f"Inventory starts at {120 * f} units. Receipts are {35 * f} and dispatches are {48 * f}. What is closing inventory?",
            107 * f,
            "Closing inventory = opening inventory + receipts − dispatches.",
        ),
        (
            "Rate normalization",
            f"Team A processes {90 * f} forms in 3 hours. Team B processes {100 * f} forms in 4 hours. How many more forms per hour does A process?",
            5 * f,
            "Compare rates: A=30f/hour, B=25f/hour. Difference=5f/hour.",
        ),
    ]
    for title, prompt, answer, explanation in cases:
        yield numeric(level, t, title, prompt, answer, explanation)


VERBAL = {
    "beginner": [
        (
            "Agreement",
            "Choose the grammatically correct sentence.",
            "Each applicant has a ticket.",
            ["Each applicant have a ticket.", "Each applicants has a ticket.", "Each applicant having a ticket."],
            "Each is singular and takes has.",
        ),
        (
            "Articles",
            "Complete: She is ___ honest colleague.",
            "an",
            ["a", "the only possible article is a", "no article"],
            "Honest begins with a vowel sound, so use an.",
        ),
        (
            "Prepositions",
            "Complete: The team is responsible ___ testing.",
            "for",
            ["at", "by", "with"],
            "Responsible for is the standard construction.",
        ),
        (
            "Tense",
            "Choose the sentence describing a finished event yesterday.",
            "We reviewed the report yesterday.",
            [
                "We review the report yesterday.",
                "We will review the report yesterday.",
                "We are review the report yesterday.",
            ],
            "A completed past event takes the simple past.",
        ),
        (
            "Concise writing",
            "Choose the clearest concise replacement for 'at this point in time'.",
            "now",
            ["never", "elsewhere", "formerly"],
            "Now retains the present-time meaning without extra words.",
        ),
        (
            "Synonym",
            "In 'a concise explanation', concise means:",
            "brief and clear",
            ["deliberately confusing", "very ancient", "unrelated"],
            "Concise writing conveys the needed information in few words.",
        ),
        (
            "Antonym",
            "Which is the opposite of optional?",
            "mandatory",
            ["flexible", "elective", "voluntary"],
            "Mandatory means required.",
        ),
        (
            "Pronouns",
            "Complete: Tara and I submitted ___ project.",
            "our",
            ["ours", "us", "we"],
            "Our is the possessive determiner before a noun.",
        ),
        (
            "Count nouns",
            "Choose the correct phrase for separate errors.",
            "fewer errors",
            ["less errors", "fewest error", "little errors"],
            "Use fewer with countable plural nouns.",
        ),
        (
            "Parallel list",
            "Choose the parallel list.",
            "reading, writing, and testing",
            ["reading, to write, and tests", "read, writing, and tested", "to read, writes, and testing"],
            "All three list elements have the same grammatical form.",
        ),
        (
            "Word choice",
            "Complete: Please ___ the invitation by Friday.",
            "accept",
            ["except", "access", "excess"],
            "Accept means agree to receive or undertake something.",
        ),
        (
            "Possession",
            "Which phrase means the laptop belongs to one developer?",
            "the developer's laptop",
            ["the developers laptop", "the developers' laptops", "the developer laptop's"],
            "A singular possessive adds apostrophe+s.",
        ),
        (
            "Sentence purpose",
            "'Could you share the agenda?' is primarily a:",
            "request",
            ["threat", "prediction", "definition"],
            "The speaker politely asks for an action.",
        ),
        (
            "Literal comprehension",
            "The notice says: 'The library closes at six except on Friday, when it closes at eight.' When does it close on Friday?",
            "8 pm",
            ["6 pm", "5 pm", "The notice does not say"],
            "Friday is explicitly the exception, with a closing time of eight.",
        ),
        (
            "Transition",
            "Complete: The task was difficult; ___, the team finished it.",
            "nevertheless",
            ["therefore", "similarly", "for example"],
            "Nevertheless signals a contrast between difficulty and completion.",
        ),
    ],
    "moderate": [
        (
            "Agreement",
            "Choose the correct sentence.",
            "Neither of the proposals is final.",
            [
                "Neither of the proposals are final.",
                "Neither proposal have final.",
                "Neither of the proposal are final.",
            ],
            "Neither as the head of this subject takes singular is.",
        ),
        (
            "Modifier",
            "Choose the sentence with a clear modifier.",
            "After reading the brief, Lena revised the design.",
            [
                "After reading the brief, the design was revised.",
                "Reading the brief, the revision appeared.",
                "The design read the brief and was revised.",
            ],
            "Lena is explicitly the person who read the brief.",
        ),
        (
            "Parallelism",
            "Choose the parallel construction.",
            "The role requires planning, coding, and testing.",
            [
                "The role requires planning, to code, and tests.",
                "The role requires plan, coding, and to test.",
                "The role requires to plan, code, and testing.",
            ],
            "Three gerunds form a parallel list.",
        ),
        (
            "Inference",
            "Every pilot participant received training. Noor was a pilot participant. What follows?",
            "Noor received training.",
            ["Noor trained every participant.", "Only Noor received training.", "Everyone trained was in the pilot."],
            "Apply the universal premise to Noor; the reverse does not follow.",
        ),
        (
            "Evidence",
            "An article says 'Sales rose after the redesign.' What alone is justified?",
            "The rise occurred later than the redesign.",
            [
                "The redesign certainly caused the rise.",
                "Nothing else affected sales.",
                "The rise will continue forever.",
            ],
            "Temporal order alone does not prove causation.",
        ),
        (
            "Tone",
            "'The proposal is promising, although the cost estimates need refinement' has what tone?",
            "constructively cautious",
            ["openly hostile", "unconditionally certain", "indifferent"],
            "It combines a positive assessment with a specific reservation.",
        ),
        (
            "Reference",
            "'Mira revised the draft after Jia commented on it.' What does 'it' most naturally refer to?",
            "the draft",
            ["Mira", "Jia", "the act of revising"],
            "The singular object being commented on is the draft.",
        ),
        (
            "Contrast",
            "Choose the transition: 'The first approach is cheaper. ___, the second is easier to maintain.'",
            "However",
            ["Therefore", "For instance", "Consequently"],
            "However contrasts two different advantages.",
        ),
        (
            "Redundancy",
            "Which edit removes redundancy without changing meaning? 'They collaborated together on the report.'",
            "They collaborated on the report.",
            ["They refused the report.", "They separately ignored the report.", "They reported no collaboration."],
            "Collaborated already means worked together.",
        ),
        (
            "Conditional",
            "'If the backup succeeds, we will deploy.' Which interpretation is supported?",
            "Deployment is conditional on backup success.",
            ["The backup has already succeeded.", "Deployment has already happened.", "Backup success is impossible."],
            "The sentence states a condition, not its fulfillment.",
        ),
        (
            "Summary",
            "A paragraph explains that remote work reduces commuting but requires deliberate communication. Choose its best summary.",
            "Remote work has benefits and coordination demands.",
            ["Remote work has no disadvantages.", "Commuting is always necessary.", "Communication is irrelevant."],
            "The summary preserves both the benefit and the qualification.",
        ),
        (
            "Usage",
            "Choose the correct use of 'affect'.",
            "The outage may affect delivery times.",
            [
                "The outage may an affect delivery times.",
                "The outage affect is delivery times.",
                "Delivery times may affects the outage.",
            ],
            "Affect is a verb meaning influence; may takes the base form.",
        ),
        (
            "Comparison",
            "Choose the logically complete comparison.",
            "This year's response rate is higher than last year's rate.",
            [
                "This year's response rate is higher than last year.",
                "This year's response is more higher.",
                "This year's rate is higher than every year person.",
            ],
            "Compare rates with rates rather than a rate with a year.",
        ),
        (
            "Active voice",
            "Choose the active-voice version of 'The patch was approved by the reviewer'.",
            "The reviewer approved the patch.",
            ["The patch was being approved.", "Approval was given to the patch.", "The approved patch was reviewed."],
            "The reviewer becomes the subject performing the action.",
        ),
        (
            "Assumption",
            "A manager argues that a reminder will reduce missed meetings. Which assumption connects the proposal to the outcome?",
            "At least some missed meetings result from forgetting.",
            ["Every meeting is unnecessary.", "No employee reads reminders.", "All absences are deliberate."],
            "A reminder addresses forgetting, so forgetting must explain some misses.",
        ),
    ],
    "pro": [
        (
            "Scope",
            "Which statement is equivalent to 'Not every approved request was processed'?",
            "At least one approved request was not processed.",
            [
                "No approved request was processed.",
                "Every request was rejected.",
                "Only processed requests were approved.",
            ],
            "The negation of a universal statement requires at least one counterexample.",
        ),
        (
            "Causal inference",
            "A training group outperformed an untrained group, but participants chose whether to attend. Which issue most directly limits causal inference?",
            "Self-selection may account for the difference.",
            ["The scores use numbers.", "Training has a name.", "The groups were observed."],
            "Pre-existing motivation or ability may influence both attendance and outcomes.",
        ),
        (
            "Necessary condition",
            "'A valid signature is necessary for approval' means:",
            "Approval implies a valid signature.",
            [
                "A valid signature guarantees approval.",
                "No approval requires a signature.",
                "Every signature is invalid.",
            ],
            "A necessary condition must hold whenever approval occurs; it may not be sufficient.",
        ),
        (
            "Quantifier order",
            "Which sentence permits a different reviewer for each report?",
            "Every report has at least one reviewer.",
            ["One reviewer reviews every report.", "No report has a reviewer.", "Exactly one reviewer exists."],
            "The reviewer can depend on the report in the first statement.",
        ),
        (
            "Qualified claim",
            "Which revision is supported by evidence from three small trials only?",
            "The early trials suggest a possible improvement.",
            ["The method always works.", "Failure is now impossible.", "All populations will benefit equally."],
            "Limited evidence supports a qualified, not universal, conclusion.",
        ),
        (
            "Alternative explanation",
            "Customer satisfaction rose after response times fell, while prices also fell. Why is the cause ambiguous?",
            "The price change is another plausible explanation.",
            ["Response time cannot be measured.", "Satisfaction cannot change.", "Two events can never coincide."],
            "Both changes may influence satisfaction, so the evidence does not isolate one cause.",
        ),
        (
            "Analogy",
            "An author compares code review to peer review to emphasize independent scrutiny. Which feature supports the analogy?",
            "Another person evaluates work before wider acceptance.",
            ["Both use identical tools.", "Both guarantee perfection.", "Both prohibit revisions."],
            "The shared relevant relation is external evaluation, not identical procedures.",
        ),
        (
            "Counterexample",
            "Which observation refutes 'All late deliveries used route A'?",
            "One late delivery used route B.",
            ["One on-time delivery used route A.", "One late delivery used route A.", "Route A exists."],
            "A universal claim is refuted by one case outside its asserted set.",
        ),
        (
            "Ambiguity",
            "'The analyst told the designer that she should revise the chart' is ambiguous because:",
            "She could refer to either person.",
            ["The chart is necessarily absent.", "Analyst is a verb.", "The sentence has no subject."],
            "Two possible antecedents compete for the pronoun.",
        ),
        (
            "Argument structure",
            "'Costs rose; therefore, the project must be cancelled' omits which most relevant consideration?",
            "Whether expected benefits still outweigh costs.",
            ["Whether costs are spelled correctly.", "Whether projects have names.", "Whether cancellation is a word."],
            "A cost increase alone does not establish that continuation is worse than cancellation.",
        ),
        (
            "Concession",
            "What is the function of 'Although the sample is small' in 'Although the sample is small, the pattern merits further study'?",
            "It acknowledges a limitation without abandoning the recommendation.",
            ["It proves the finding universally.", "It denies any pattern.", "It states the final cause."],
            "A concessive clause admits a concern while maintaining the main claim.",
        ),
        (
            "Correlation",
            "Two metrics move together across departments. Which conclusion is most careful?",
            "They are associated in these observations; causation remains unresolved.",
            [
                "One necessarily causes the other.",
                "The relationship must hold forever.",
                "No third variable can matter.",
            ],
            "Association can arise through causation, confounding or other mechanisms.",
        ),
        (
            "Precision",
            "Which statement distinguishes absence of evidence from evidence of absence?",
            "No fault was detected; the test may still miss some faults.",
            [
                "No fault was detected, so none can exist.",
                "Every test detects every fault.",
                "Testing is logically impossible.",
            ],
            "A test's sensitivity limits what a negative result establishes.",
        ),
        (
            "Restrictive meaning",
            "Which sentence limits the extension to applicants who submitted on time?",
            "Applicants who submitted on time received an extension.",
            [
                "All applicants received an extension regardless of submission.",
                "No timely applicant received an extension.",
                "Every extension prevented submission.",
            ],
            "The restrictive relative clause narrows which applicants the sentence describes.",
        ),
        (
            "Best synthesis",
            "One study finds speed gains; another finds more errors under the same workflow. Which synthesis preserves both findings?",
            "The workflow may trade accuracy for speed.",
            [
                "Both studies prove zero change.",
                "Errors are impossible when speed rises.",
                "The workflow is universally superior.",
            ],
            "A trade-off interpretation accommodates both the improvement and the cost.",
        ),
    ],
}

REFLECTIONS = [
    ("Planning", "I break a large task into smaller steps before starting."),
    ("Feedback", "I ask for specific feedback when I am unsure how to improve."),
    ("Collaboration", "I make space for quieter teammates to share their ideas."),
    ("Adaptability", "I can revise my approach when new evidence challenges my plan."),
    ("Follow through", "I communicate early when I may miss a commitment."),
    ("Learning", "I set aside time to understand why a mistake happened."),
    ("Focus", "I reduce avoidable distractions when doing demanding work."),
    ("Clarification", "I clarify unclear requirements before investing substantial effort."),
    ("Initiative", "I look for useful next steps when my assigned work is finished."),
    ("Disagreement", "I can question an idea while treating the person respectfully."),
    ("Priorities", "I distinguish urgent tasks from important longer-term work."),
    ("Help seeking", "I seek help after a reasonable independent attempt."),
    ("Reliability", "I check important details before sharing a deliverable."),
    ("Reflection", "I notice which working conditions help me do my best work."),
    ("Ownership", "I acknowledge my contribution when a team outcome falls short."),
]


def build_questions():
    for k, level in enumerate(LEVELS):
        yield from quant(level, k)
        yield from logical(level, k)
        yield from interpretation(level, k)
        for title, prompt, answer, wrong, explanation in VERBAL[level]:
            yield item(level, TOPICS[2], title, prompt, answer, wrong, explanation)
    for i, (title, prompt) in enumerate(REFLECTIONS):
        yield dict(
            slug=f"pf-reflection-{i + 1}",
            type="reflection",
            title=title,
            question=prompt,
            options=["Strongly disagree", "Disagree", "Neither agree nor disagree", "Agree", "Strongly agree"],
            correct_answer=None,
            explanation="There is no correct answer. Reflect on a recent example and one practical habit you would like to develop. This is not a validated psychological or hiring assessment.",
            difficulty="moderate",
            topic=TOPICS[4],
            subtopic=title,
            tags=["original", "unscored-reflection"],
            estimated_time=45,
        )


def seed_mixed(db):
    from sqlalchemy import select

    from .admin import QuestionInput, save_question
    from .models import Question

    inserted = 0
    for data in build_questions():
        if not db.scalar(select(Question).where(Question.slug == data["slug"])):
            save_question(db, QuestionInput.model_validate(data))
            inserted += 1
        db.commit()  # Keep Atlas transactions bounded, and seeding safely resumable.
    return inserted


if __name__ == "__main__":
    from .db import SessionLocal

    with SessionLocal() as db:
        print("Original mixed-set questions added:", seed_mixed(db))
