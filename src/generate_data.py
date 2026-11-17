"""Generate the project's explicitly synthetic skill taxonomy and example data.

Run from any directory with: python src/generate_data.py
All descriptions, organizations, postings, and student profiles emitted here are
synthetic. Ground-truth skill columns are generated from the same taxonomy.
"""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SEED = 20261117


# Each tuple is (canonical skill, curated aliases). This list is the source of
# truth for skills.json and contains 300 skills across five requested areas.
TAXONOMY = {
    "software": [
        ("Python", ["py", "Python 3"]), ("Java", ["Java SE"]), ("C", ["C language"]), ("C++", ["CPP", "C plus plus"]),
        ("C#", ["C sharp", "C-sharp"]), ("Go", ["Golang"]), ("Rust", ["Rust lang"]), ("Ruby", ["Ruby language"]),
        ("PHP", ["PHP language"]), ("Kotlin", ["Kotlin JVM"]), ("Swift", ["Swift language"]), ("Scala", ["Scala language"]),
        ("Bash", ["Bash scripting", "shell scripting"]), ("PowerShell", ["Powershell scripting"]), ("SQL", ["structured query language"]),
        ("Object-oriented programming", ["OOP", "object oriented design"]), ("Functional programming", ["FP"]), ("Concurrency", ["concurrent programming"]),
        ("Multithreading", ["multi-threading", "threads"]), ("Data structures", ["DS", "data structure design"]),
        ("Algorithms", ["algorithm design", "problem solving"]), ("Design patterns", ["software patterns"]), ("System design", ["software architecture"]),
        ("Clean code", ["readable code", "code quality"]), ("Code review", ["peer review"]), ("Debugging", ["troubleshooting code"]),
        ("Unit testing", ["unit tests"]), ("Integration testing", ["integration tests"]), ("Test-driven development", ["TDD"]),
        ("Behavior-driven development", ["BDD"]), ("Continuous integration", ["CI"]), ("Continuous delivery", ["CD", "continuous deployment"]),
        ("Git", ["version control", "git workflow"]), ("GitHub", ["GitHub collaboration"]), ("GitLab", ["GitLab CI"]),
        ("Linux", ["GNU/Linux"]), ("Operating systems", ["OS concepts"]), ("Networking fundamentals", ["computer networking"]),
        ("TCP/IP", ["TCP IP stack"]), ("DNS", ["domain name system"]), ("HTTP", ["HTTP protocol"]),
        ("Security fundamentals", ["application security basics"]), ("OAuth", ["OAuth 2.0"]), ("JWT", ["JSON Web Token"]),
        ("Cryptography fundamentals", ["encryption basics"]), ("API development", ["API design", "built REST services"]),
        ("REST APIs", ["RESTful services", "REST endpoints"]), ("GraphQL", ["GraphQL APIs"]), ("gRPC", ["Google RPC"]),
        ("Microservices", ["microservice architecture"]), ("Event-driven architecture", ["EDA"]), ("Message queues", ["message brokers"]),
        ("Apache Kafka", ["Kafka"]), ("RabbitMQ", ["AMQP"]), ("Caching", ["cache design"]),
        ("Redis", ["Redis cache"]), ("Memcached", ["memory caching"]), ("Relational databases", ["RDBMS"]),
        ("Database design", ["schema design"]), ("Database normalization", ["normalization"]), ("PostgreSQL", ["Postgres"]),
        ("MySQL", ["MariaDB"]), ("SQLite", ["embedded SQL database"]), ("Microsoft SQL Server", ["MSSQL", "SQL Server"]),
        ("Oracle Database", ["Oracle DB"]), ("NoSQL databases", ["NoSQL"]), ("MongoDB", ["Mongo"]),
        ("Cassandra", ["Apache Cassandra"]), ("Elasticsearch", ["Elastic Search"]), ("Redis data structures", ["Redis commands"]),
        ("ORMs", ["object relational mapping"]), ("Hibernate", ["Java ORM"]), ("SQLAlchemy", ["Python ORM"]),
        ("Prisma", ["Prisma ORM"]), ("JDBC", ["Java Database Connectivity"]), ("Build systems", ["build tooling"]),
        ("Maven", ["Apache Maven"]), ("Gradle", ["Gradle build"]), ("CMake", ["CMake build"]),
        ("Dependency management", ["package management"]), ("npm", ["Node package manager"]), ("pip", ["Python package installer"]),
        ("Documentation", ["technical documentation"]), ("Technical writing", ["developer writing"]), ("CLI development", ["command-line tools"]),
        ("Regular expressions", ["regex"]), ("Unicode", ["character encoding"]), ("Compiler fundamentals", ["compiler design basics"]),
        ("Interpreter design", ["language runtimes"]), ("Memory management", ["memory allocation"]), ("Garbage collection", ["GC"]),
        ("Performance profiling", ["profiling"]), ("Optimization", ["code optimization"]), ("Refactoring", ["code refactoring"]),
        ("Legacy code maintenance", ["legacy systems"]), ("Pair programming", ["paired coding"]), ("Agile software development", ["Agile"]),
        ("Scrum", ["Scrum framework"]), ("Kanban", ["Kanban workflow"]), ("Technical interviewing", ["coding interviews"]),
        ("Open-source contribution", ["open source"]), ("Software licensing", ["OSS licenses"]), ("Accessibility in software", ["inclusive software"]),
    ],
    "data_ml": [
        ("Data analysis", ["data analytics"]), ("Data cleaning", ["data wrangling", "data preparation"]), ("Exploratory data analysis", ["EDA", "exploratory analysis"]),
        ("Statistics", ["statistical analysis"]), ("Probability", ["probability theory"]), ("Linear algebra", ["matrix algebra"]),
        ("Calculus", ["differential calculus"]), ("Hypothesis testing", ["statistical tests"]), ("A/B testing", ["split testing"]),
        ("Experimental design", ["experiment design"]), ("Causal inference", ["causal analysis"]), ("Time series analysis", ["time-series"]),
        ("Forecasting", ["demand forecasting"]), ("Regression", ["regression analysis"]), ("Classification", ["classification models"]),
        ("Clustering", ["cluster analysis"]), ("Dimensionality reduction", ["PCA", "feature reduction"]), ("Feature engineering", ["feature creation"]),
        ("Model evaluation", ["model validation"]), ("Cross-validation", ["cross validation"]), ("Hyperparameter tuning", ["parameter search"]),
        ("Scikit-learn", ["sklearn", "scikit learn"]), ("PyTorch", ["torch"]), ("TensorFlow", ["tf"]),
        ("Keras", ["keras API"]), ("XGBoost", ["extreme gradient boosting"]), ("LightGBM", ["light gradient boosting"]),
        ("CatBoost", ["categorical boosting"]), ("Gradient boosting", ["GBDT"]), ("Random forests", ["random forest"]),
        ("Decision trees", ["tree models"]), ("Support vector machines", ["SVM"]), ("Nearest neighbors", ["KNN", "k-nearest neighbors"]),
        ("Naive Bayes", ["NB classifier"]), ("Ensemble learning", ["model ensembles"]), ("Neural networks", ["artificial neural networks"]),
        ("Deep learning", ["DL"]), ("Convolutional neural networks", ["CNN"]), ("Recurrent neural networks", ["RNN"]),
        ("Transformers", ["transformer models"]), ("Attention mechanisms", ["self-attention"]), ("Large language models", ["LLMs", "generative language models"]),
        ("Prompt engineering", ["prompt design"]), ("Retrieval-augmented generation", ["RAG"]), ("Fine-tuning language models", ["LLM fine tuning"]),
        ("Natural language processing", ["NLP"]), ("Text classification", ["document classification"]), ("Named entity recognition", ["NER"]),
        ("Information retrieval", ["search and retrieval"]), ("Text embeddings", ["sentence embeddings"]), ("Vector databases", ["vector stores"]),
        ("Computer vision", ["CV"]), ("Image classification", ["visual classification"]), ("Object detection", ["object recognition"]),
        ("Image segmentation", ["semantic segmentation"]), ("OpenCV", ["Open Computer Vision"]), ("Recommendation systems", ["recommender systems"]),
        ("Reinforcement learning", ["RL"]), ("MLOps", ["machine learning operations"]), ("Model deployment", ["serving ML models"]),
        ("Model monitoring", ["ML monitoring"]), ("Data pipelines", ["data workflows"]), ("ETL", ["extract transform load"]),
        ("ELT", ["extract load transform"]), ("Apache Spark", ["Spark"]), ("PySpark", ["Python Spark"]),
        ("Apache Hadoop", ["Hadoop"]), ("Apache Airflow", ["Airflow"]), ("dbt", ["data build tool"]),
        ("Pandas", ["Python pandas"]), ("NumPy", ["numerical Python"]), ("Polars", ["Polars dataframe"]),
        ("Jupyter", ["Jupyter notebooks"]), ("Matplotlib", ["pyplot"]), ("Seaborn", ["statistical plotting"]),
        ("Plotly", ["interactive charts"]), ("Tableau", ["Tableau dashboards"]), ("Power BI", ["Microsoft Power BI"]),
        ("Looker", ["Looker BI"]), ("Data visualization", ["data viz"]), ("Dashboard design", ["dashboarding"]),
        ("Business intelligence", ["BI"]), ("Data modeling", ["analytical data modeling"]), ("Data warehousing", ["data warehouse"]),
        ("Snowflake", ["Snowflake data platform"]), ("BigQuery", ["Google BigQuery"]), ("Amazon Redshift", ["Redshift"]),
        ("Delta Lake", ["Delta tables"]), ("Data governance", ["data stewardship"]), ("Data quality", ["data validation"]),
        ("Data privacy", ["privacy-preserving data"]), ("Synthetic data generation", ["artificial data"]), ("Knowledge graphs", ["graph data"]),
        ("Graph neural networks", ["GNN"]), ("Bayesian methods", ["Bayesian statistics"]), ("Optimization methods", ["mathematical optimization"]),
        ("Geospatial analysis", ["GIS analytics"]), ("SQL analytics", ["analytical SQL"]), ("Scientific computing", ["numerical computing"]),
        ("ML experiment tracking", ["experiment tracking"]), ("Weights & Biases", ["W&B", "wandb"]),
    ],
    "web": [
        ("HTML", ["HTML5"]), ("CSS", ["CSS3", "cascading style sheets"]), ("JavaScript", ["JS", "ECMAScript"]),
        ("TypeScript", ["TS"]), ("Node.js", ["Node", "node.js backend"]), ("React", ["React.js", "ReactJS"]),
        ("Next.js", ["NextJS"]), ("Vue.js", ["Vue", "VueJS"]), ("Angular", ["Angular framework"]),
        ("Svelte", ["SvelteKit"]), ("jQuery", ["jQuery library"]), ("Web components", ["custom elements"]),
        ("DOM manipulation", ["Document Object Model"]), ("Responsive design", ["mobile-first design"]), ("CSS Grid", ["grid layout"]),
        ("Flexbox", ["CSS flexbox"]), ("Sass", ["SCSS"]), ("Tailwind CSS", ["Tailwind"]),
        ("Bootstrap", ["Bootstrap CSS"]), ("Material UI", ["MUI"]), ("Web accessibility", ["WCAG", "a11y"]),
        ("Frontend testing", ["UI testing"]), ("Jest", ["Jest testing"]), ("Playwright", ["browser automation"]),
        ("Cypress", ["Cypress testing"]), ("Web performance", ["frontend performance"]), ("Progressive web apps", ["PWA"]),
        ("Service workers", ["web workers"]), ("Browser storage", ["local storage"]), ("WebSockets", ["WebSocket protocol"]),
        ("Server-side rendering", ["SSR"]), ("Static site generation", ["SSG"]), ("Vite", ["Vite bundler"]),
        ("Webpack", ["webpack bundler"]), ("REST client integration", ["fetch API", "Axios"]), ("FastAPI", ["Fast API"]),
        ("Django", ["Django framework"]), ("Flask", ["Flask framework"]), ("Fastify", ["Fastify Node"]),
        ("Express.js", ["Express", "ExpressJS"]), ("NestJS", ["Nest.js"]), ("Spring Boot", ["Spring framework"]),
        ("ASP.NET Core", [".NET Core web"]), ("Laravel", ["Laravel PHP"]), ("Ruby on Rails", ["Rails"]),
        ("Web authentication", ["login flows"]), ("Session management", ["web sessions"]), ("Web security", ["OWASP"]),
        ("Content security policy", ["CSP headers"]), ("Cross-site scripting prevention", ["XSS prevention"]), ("CSRF protection", ["cross-site request forgery"]),
        ("Responsive email design", ["HTML email"]), ("SEO fundamentals", ["search engine optimization"]), ("Web analytics", ["website analytics"]),
        ("Design systems", ["UI design systems"]), ("Figma handoff", ["design-to-code"]), ("Internationalization", ["i18n"]),
        ("Localization", ["l10n"]), ("GraphQL client integration", ["Apollo Client"]), ("OpenAPI", ["Swagger"]),
        ("API documentation", ["endpoint documentation"]), ("Web scraping", ["website scraping"]), ("Playwright scraping", ["browser-based scraping"]),
        ("Web components testing", ["component testing"]), ("State management", ["client state"]), ("Redux", ["Redux Toolkit"]),
        ("Zustand", ["Zustand state management"]), ("TanStack Query", ["React Query"]), ("Form validation", ["form handling"]),
        ("Web forms", ["HTML forms"]), ("Templating engines", ["server templates"]), ("Handlebars", ["Mustache templates"]),
        ("E-commerce development", ["online storefronts"]), ("Payment integration", ["payment gateways"]), ("Web deployment", ["frontend deployment"]),
    ],
    "embedded": [
        ("Embedded C", ["C for microcontrollers"]), ("Embedded C++", ["C++ firmware"]), ("Microcontrollers", ["MCUs"]),
        ("Arduino", ["Arduino IDE"]), ("ESP32", ["ESP32 development"]), ("Raspberry Pi", ["Raspberry Pi boards"]),
        ("STM32", ["STM32 microcontrollers"]), ("ARM architecture", ["ARM Cortex"]), ("RISC-V", ["RISC V"]),
        ("Firmware development", ["firmware engineering"]), ("Real-time systems", ["RTOS concepts"]), ("FreeRTOS", ["Free RTOS"]),
        ("Zephyr RTOS", ["Zephyr"]), ("Embedded Linux", ["Linux on embedded devices"]), ("Device drivers", ["driver development"]),
        ("Bare-metal programming", ["bare metal"]), ("Interrupt handling", ["interrupt service routines"]), ("Direct memory access", ["DMA"]),
        ("Memory-mapped I/O", ["MMIO"]), ("UART", ["serial communication"]), ("SPI", ["Serial Peripheral Interface"]),
        ("I2C", ["I squared C"]), ("CAN bus", ["Controller Area Network"]), ("USB", ["USB protocol"]),
        ("Ethernet", ["wired networking"]), ("BLE", ["Bluetooth Low Energy"]), ("Bluetooth", ["Bluetooth Classic"]),
        ("Wi-Fi", ["802.11 networking"]), ("LoRaWAN", ["LoRa"]), ("Zigbee", ["ZigBee"]),
        ("MQTT", ["Message Queuing Telemetry Transport"]), ("Modbus", ["Modbus protocol"]), ("IoT", ["Internet of Things"]),
        ("Sensor integration", ["sensor interfacing"]), ("Actuator control", ["motor and actuator control"]), ("Analog-to-digital conversion", ["ADC"]),
        ("Digital-to-analog conversion", ["DAC"]), ("Pulse-width modulation", ["PWM"]), ("Signal processing", ["digital signal processing"]),
        ("Digital signal processing", ["DSP"]), ("Control systems", ["feedback control"]), ("PID control", ["proportional integral derivative"]),
        ("Robotics", ["robot control"]), ("ROS", ["Robot Operating System"]), ("PCB design", ["printed circuit board design"]),
        ("KiCad", ["KiCad EDA"]), ("Altium Designer", ["Altium"]), ("Circuit analysis", ["electronics fundamentals"]),
        ("Schematic capture", ["circuit schematics"]), ("Electronics prototyping", ["breadboarding"]), ("Hardware debugging", ["board bring-up"]),
        ("Oscilloscope", ["scope measurements"]), ("Logic analyzer", ["digital logic analyzer"]), ("JTAG", ["Joint Test Action Group"]),
        ("SWD debugging", ["Serial Wire Debug"]), ("Hardware-in-the-loop testing", ["HIL testing"]), ("Unit testing embedded software", ["firmware unit tests"]),
        ("Power management", ["low-power design"]), ("Battery systems", ["battery management"]), ("Sensor fusion", ["multi-sensor fusion"]),
        ("Computer architecture", ["CPU architecture"]), ("Digital logic", ["logic design"]), ("FPGA basics", ["field programmable gate arrays"]),
        ("Verilog", ["Verilog HDL"]), ("VHDL", ["VHSIC hardware description language"]), ("Hardware description languages", ["HDL"]),
        ("Edge computing", ["on-device computing"]), ("Embedded security", ["secure firmware"]), ("Secure boot", ["verified boot"]),
        ("OTA updates", ["over-the-air firmware updates"]), ("Device provisioning", ["IoT provisioning"]), ("Telemetry", ["device telemetry"]),
        ("Embedded systems testing", ["hardware software testing"]), ("Manufacturing test", ["production test"]), ("DFM", ["design for manufacturing"]),
    ],
    "professional": [
        ("Communication", ["clear communication"]), ("Written communication", ["professional writing"]), ("Presentation skills", ["presenting"]),
        ("Teamwork", ["collaboration"]), ("Cross-functional collaboration", ["working across teams"]), ("Problem solving", ["analytical problem solving"]),
        ("Critical thinking", ["reasoned judgment"]), ("Creativity", ["creative thinking"]), ("Adaptability", ["flexibility"]),
        ("Initiative", ["self-starter"]), ("Ownership", ["accountability"]), ("Time management", ["prioritization"]),
        ("Organization", ["organizational skills"]), ("Attention to detail", ["detail oriented"]), ("Leadership", ["team leadership"]),
        ("Mentoring", ["peer mentoring"]), ("Conflict resolution", ["mediation"]), ("Negotiation", ["negotiating"]),
        ("Customer empathy", ["user empathy"]), ("Stakeholder management", ["stakeholder communication"]), ("Requirements gathering", ["eliciting requirements"]),
        ("Project management", ["project planning"]), ("Risk management", ["project risk"]), ("Decision making", ["sound judgment"]),
        ("Research", ["desk research"]), ("Literature review", ["reviewing research"]), ("Technical presentation", ["engineering presentations"]),
        ("Meeting facilitation", ["facilitating meetings"]), ("Documentation habits", ["keeping project notes"]), ("Remote collaboration", ["distributed teamwork"]),
        ("Intercultural communication", ["cross-cultural communication"]), ("Ethical reasoning", ["professional ethics"]), ("Data ethics", ["responsible data use"]),
        ("Privacy awareness", ["privacy by design"]), ("Security awareness", ["secure working practices"]), ("Learning agility", ["rapid learning"]),
        ("Self-directed learning", ["independent learning"]), ("Feedback literacy", ["giving and receiving feedback"]), ("Resilience", ["persistence"]),
        ("Professional networking", ["career networking"]), ("Career planning", ["career development"]), ("Portfolio development", ["project portfolio"]),
        ("Resume writing", ["CV writing"]), ("Interview skills", ["job interview preparation"]), ("Business awareness", ["commercial awareness"]),
        ("Product thinking", ["product sense"]), ("User-centered design", ["human-centered design"]), ("Design thinking", ["human-centered problem solving"]),
        ("Service orientation", ["customer service"]), ("Sustainability awareness", ["environmental awareness"]), ("Quality mindset", ["commitment to quality"]),
        ("Process improvement", ["continuous improvement"]), ("Entrepreneurship", ["entrepreneurial thinking"]), ("Innovation management", ["innovation"]),
        ("Budget awareness", ["cost awareness"]), ("Consulting skills", ["client advisory"]), ("Teaching", ["instruction"]),
        ("Tutoring", ["academic tutoring"]), ("Facilitation", ["group facilitation"]), ("Volunteer coordination", ["volunteer management"]),
        ("Event planning", ["event coordination"]), ("Public speaking", ["speaking to groups"]), ("English proficiency", ["professional English"]),
        ("Multilingual communication", ["multilingual skills"]), ("Inclusive teamwork", ["inclusive collaboration"]), ("Meeting notes", ["minutes taking"]),
        ("Task estimation", ["effort estimation"]), ("Work planning", ["planning work"]), ("Deadline management", ["meeting deadlines"]),
        ("Professionalism", ["workplace conduct"]), ("Reliability", ["dependability"]), ("Self-awareness", ["reflective practice"]),
        ("Emotional intelligence", ["EQ"]), ("Listening", ["active listening"]), ("Persuasion", ["influencing"]),
        ("Facilitating workshops", ["workshop facilitation"]), ("Knowledge sharing", ["sharing technical knowledge"]), ("Portfolio storytelling", ["explaining projects"]),
        ("Scientific communication", ["communicating research"]), ("Policy awareness", ["regulatory awareness"]), ("Change management", ["organizational change"]),
    ],
}


PHRASES = {
    "Python": ["wrote small Python tools", "automated tasks with py", "built scripts in Python 3"],
    "JavaScript": ["built interactive browser features in JS", "used ECMAScript for UI behavior", "wrote client-side JavaScript"],
    "API development": ["built REST services", "created endpoints for other teams", "designed service interfaces"],
    "Data analysis": ["explored datasets to answer questions", "turned raw tables into findings", "analyzed messy records"],
    "Machine Learning": ["trained predictive models", "applied learning algorithms", "built ML prototypes"],
    "React": ["assembled interfaces with React", "built component-based screens", "used ReactJS on the client"],
    "SQL": ["queried relational data", "wrote database queries", "used structured query language"],
    "Git": ["tracked changes with Git", "worked through version control", "managed branches and commits"],
    "Embedded C": ["wrote low-level firmware in C", "programmed microcontroller firmware", "worked close to the hardware"],
    "Communication": ["shared progress clearly with teammates", "explained technical work to others", "kept collaborators informed"],
}


def records():
    return [
        {"canonical_name": name, "category": category, "aliases": aliases}
        for category, skills in TAXONOMY.items()
        for name, aliases in skills[:60]
    ]


def phrase_for(skill: str, rng: random.Random) -> str:
    if skill in PHRASES:
        return rng.choice(PHRASES[skill])
    return rng.choice([f"hands-on experience with {skill}", f"used {skill} in coursework", f"worked on projects involving {skill}"])


def make_internships(skills, rng):
    rows = []
    titles = ["Software Engineering Intern", "Data Science Intern", "Web Platform Intern", "Embedded Systems Intern", "Technology Project Intern", "Research Engineering Intern"]
    companies = ["Northstar Labs", "Cedarbridge Systems", "Blue Finch Software", "Orbit Forge", "Maple Circuit Works", "Open Current Studio", "Silverline Analytics", "Harborlight Tech"]
    openings = ["Join a small team working on", "Help us improve", "Contribute to", "Work alongside engineers on", "Explore practical problems in", "Build and maintain"]
    contexts = ["production tools used by internal teams", "a student-facing product", "connected devices and their services", "data workflows for research", "accessible web experiences", "reliable software prototypes"]
    for i in range(600):
        required = rng.sample(skills, rng.randint(4, 8))
        remaining = [s for s in skills if s not in required]
        preferred = rng.sample(remaining, rng.randint(2, 5))
        wording = ". ".join(f"{rng.choice(openings)} {phrase_for(s, rng)}" for s in rng.sample(required, min(3, len(required))))
        description = (f"SYNTHETIC POSTING. {wording}. The work touches {rng.choice(contexts)}. "
                       f"You will share progress with a collaborative group and document what you learn. "
                       f"Useful background includes {', '.join(phrase_for(s, rng) for s in rng.sample(preferred, min(2, len(preferred))))}.")
        rows.append({"title": rng.choice(titles), "company": f"{rng.choice(companies)} {i + 1:03d}",
                     "description": description, "required_skills": "|".join(required),
                     "preferred_skills": "|".join(preferred)})
    return rows


def make_students(skills, rng):
    rows = []
    starts = ["In class and personal projects,", "My recent work has included", "I have been learning by", "Outside lectures,", "Across team assignments,"]
    endings = ["I enjoy learning from feedback and collaborating across disciplines.", "I am looking for a placement where I can keep building practical experience.", "I like turning an unclear problem into a small working prototype.", "I document decisions and share progress as I go."]
    for i in range(360):
        true_skills = rng.sample(skills, rng.randint(6, 12))
        selected = rng.sample(true_skills, min(5, len(true_skills)))
        prose = f"{rng.choice(starts)} {', '.join(phrase_for(s, rng) for s in selected)}. {rng.choice(endings)}"
        rows.append({"profile": f"SYNTHETIC STUDENT PROFILE. {prose}", "true_skills": "|".join(true_skills)})
    return rows


def write_csv(path: Path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    taxonomy = records()
    if len(taxonomy) != len({entry["canonical_name"] for entry in taxonomy}):
        raise ValueError("Taxonomy contains duplicate canonical names")
    (DATA / "skills.json").write_text(json.dumps(taxonomy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rng = random.Random(SEED)
    names = [entry["canonical_name"] for entry in taxonomy]
    write_csv(DATA / "internships.csv", make_internships(names, rng), ["title", "company", "description", "required_skills", "preferred_skills"])
    write_csv(DATA / "students.csv", make_students(names, rng), ["profile", "true_skills"])
    print(f"Generated {len(taxonomy)} taxonomy entries, 600 synthetic internships, and 360 synthetic student profiles.")


if __name__ == "__main__":
    main()
