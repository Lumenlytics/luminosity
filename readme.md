🎓 Luminosity School Management System
A comprehensive synthetic educational dataset spanning 10 years of realistic school operations (2016-2026)

Tech Stack: Python 3.10+ | PostgreSQL | Supabase | 2GB+ Dataset | 650K+ Records

📖 Overview
Luminosity is a production-ready synthetic school management dataset designed for educational research, software testing, and data science applications. The system simulates a complete K-12 private academy with 500+ students, 60+ teachers, and comprehensive academic operations across a full decade.

🎯 Key Features
🏫 Complete School Ecosystem: Students, teachers, classes, grades, attendance, finances
📅 10-Year Historical Data: Longitudinal dataset from 2016-2026 with realistic progression
👨‍🎓 Student Lifecycles: Full K-12 journeys with graduation, enrollment, and transfer modeling
👩‍🏫 Teacher Career Progression: Realistic staff turnover, promotions, and professional development
📊 Policy-Compliant Data: Attendance rates, grade distributions, and academic policies
🦠 Real-World Events: COVID-19 impact modeling for 2020-2021 academic year
🔍 Comprehensive Validation: Multi-layer quality assurance and data integrity checks
☁️ Cloud-Ready: Supabase integration with automated deployment scripts
📊 Dataset Statistics
Metric	Value	Description
School Years	10	Complete academic years (2016-2026)
Students	5,500+	Including alumni and current enrollment
Teachers	150+	Across all years with career progression
Grade Records	650,000+	Individual assignment scores
Attendance Records	1,000,000+	Daily attendance tracking
Classes	800+	Course sections across the decade
Database Size	~2GB	Compressed educational data
🏗️ Project Structure
luminosity/
├── 📁 data/
│   ├── 📁 decade/           # 10-year historical data by academic year
│   │   ├── 📁 2016-2017/    # Complete school year dataset
│   │   ├── 📁 2017-2018/    # Student progression year 2
│   │   ├── ...              # Additional years
│   │   └── 📁 2025-2026/    # Most recent academic year
│   ├── 📁 combined_csv/     # Aggregated decade-spanning datasets
│   ├── 📁 clean_csv/        # Base year data (2015-2016)
│   └── 📁 test/             # Sample data for development
├── 📁 scripts/              # Data generation and utility tools
│   ├── complete_decade_generator.py   # Main data generation orchestrator
│   ├── decade_uploader.py             # Supabase cloud deployment
│   ├── validate_decade_data.py        # Quality assurance validator
│   └── upload_to_supabase.py          # Database integration
├── 📁 schema/               # Database schema and documentation
│   ├── luminosity_schema_enhanced.sql # Production database schema
│   ├── luminosity_schema.mmd          # Entity relationship diagram
│   └── constraints_and_indexes.sql    # Performance optimization
├── 📁 docs/                 # Documentation and analysis
│   ├── Document_of_Truth.docx         # Business rules and policies
│   ├── 10_Year_Expansion_Plan.md      # Development roadmap
│   └── Data_Quality_Analysis.md       # Validation methodology
└── 📄 README.md             # This file
🚀 Quick Start
Prerequisites
Python 3.10+ with pandas, numpy, faker
PostgreSQL 12+ or Supabase account
Git for repository management
1. Clone Repository
bash
git clone https://github.com/lumenlytics/luminosity.git
cd luminosity
2. Set Up Environment
bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install pandas numpy faker python-dotenv supabase
3. Configure Database Connection
bash
# Copy environment template
cp .env.example .env

# Edit .env with your Supabase credentials
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
4. Deploy to Database
bash
# Upload decade dataset to Supabase
cd scripts
python decade_uploader.py --validate --report

# Or upload specific year
python upload_to_supabase.py --year 2024-2025
5. Explore the Data
bash
# Generate validation report
python validate_decade_data.py --detailed

# Analyze specific metrics
python analyze_upload_failures.py --summary
📚 Data Model Overview
Core Entities
👥 People Management

Students: Demographics, grade progression, academic history
Teachers: Career progression, department assignments, certifications
Guardians: Family relationships, contact information, payment history
📖 Academic Operations

Classes: Course sections with teacher and student assignments
Assignments: Homework, tests, projects with realistic due dates
Grades: Individual scores following educational distribution policies
Attendance: Daily tracking with absence/tardy pattern compliance
🏫 Administrative Systems

School Calendar: Holidays, breaks, professional development days
Financial Management: Tuition, fees, payment plans, scholarships
Discipline Reports: Incident tracking and intervention documentation
Key Relationships
mermaid
erDiagram
    STUDENTS ||--o{ GRADES : earns
    STUDENTS ||--o{ ATTENDANCE : has
    STUDENTS ||--o{ ENROLLMENTS : participates
    TEACHERS ||--o{ CLASSES : teaches
    CLASSES ||--o{ ASSIGNMENTS : contains
    ASSIGNMENTS ||--o{ GRADES : receives
    GUARDIANS ||--o{ PAYMENTS : makes
    GUARDIANS ||--o{ STUDENTS : manages
🎯 Use Cases
📊 Educational Research
Longitudinal Studies: Track student performance over time
Policy Impact Analysis: Measure effects of curriculum changes
Demographic Studies: Analyze achievement gaps and trends
Predictive Modeling: Graduation outcome forecasting
💻 Software Development
System Testing: Realistic data for school management software
Performance Benchmarking: Database optimization with real-world volumes
API Development: RESTful services with comprehensive test data
UI/UX Testing: Authentic user scenarios and edge cases
🧠 Data Science & ML
Classification Models: Student success prediction algorithms
Time Series Analysis: Attendance pattern recognition
Clustering Analysis: Student performance groupings
Natural Language Processing: Assignment text analysis
🏫 Administrative Training
Staff Onboarding: Realistic scenarios for new administrators
Policy Simulation: Test new procedures without real student impact
Report Generation: Practice with comprehensive academic reporting
Emergency Planning: Attendance and contact data for crisis scenarios
📈 Data Quality Assurance
Validation Framework
Our comprehensive validation ensures research-grade data quality:

✅ Referential Integrity: All foreign key relationships validated
✅ Business Rule Compliance: Attendance rates, grade distributions per policy
✅ Temporal Consistency: Logical progression across academic years
✅ Statistical Accuracy: Realistic distributions matching real-world patterns
✅ Educational Authenticity: Curriculum alignment with standards
Quality Metrics
Validation Check	Target	Actual	Status
Attendance Rate	95% ± 2%	94.8%	✅ Pass
Grade Distribution	70-100 range, 87 median	86.9 median	✅ Pass
Graduation Rate	95%+	96.2%	✅ Pass
Data Completeness	99%+	99.7%	✅ Pass
Referential Integrity	100%	100%	✅ Pass
🛠️ Advanced Features
COVID-19 Impact Modeling (2020-2021)
Realistic simulation of pandemic effects on education:

Hybrid Learning: Modified attendance patterns and grading policies
Technology Adaptation: Increased digital tool usage
Academic Adjustments: Pass/fail options and modified assessments
Health Protocols: Enhanced screening and modified schedules
Student Progression Modeling
Realistic Educational Journeys:

Grade advancement with academic performance correlation
Transfer students with mid-year enrollment patterns
Special needs accommodations and individualized learning plans
Gifted programs and advanced placement tracking
Teacher Career Simulation
Professional Development Lifecycle:

New teacher mentorship and certification progression
Department leadership rotations and administrative advancement
Professional development and continuing education tracking
Retirement planning and succession management
🔧 Configuration & Customization
Environment Variables
bash
# Database Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_service_role_key

# Data Generation Settings
RANDOM_SEED=42                    # For reproducible datasets
TOTAL_STUDENTS=500               # Base enrollment size
ABSENCE_RATE=0.05                # 5% absence policy
TARDY_RATE=0.03                  # 3% tardy policy
GRADE_MEDIAN=87                  # Target grade distribution

# Upload Configuration
BATCH_SIZE=1000                  # Records per batch upload
MAX_RETRIES=3                    # Upload retry attempts
VALIDATION_LEVEL=strict          # Data quality enforcement
Customization Options
Academic Policies: Modify grading scales, attendance requirements, and curriculum standards Demographics: Adjust student population size, grade level distribution, and family structures Financial Models: Configure tuition rates, fee structures, and payment plan options Calendar Settings: Customize school year dates, holiday schedules, and break periods

📋 API Reference
Core Data Access Patterns
python
# Student academic history
def get_student_transcript(student_id, year_range=None):
    """Retrieve complete academic record for student"""
    
# Teacher performance metrics
def analyze_teacher_effectiveness(teacher_id, metrics=['grades', 'attendance']):
    """Calculate teacher impact on student outcomes"""
    
# School-wide analytics
def generate_annual_report(school_year, include_comparisons=True):
    """Comprehensive school performance analysis"""
Database Views
Ready-to-use analytical views:

v_current_students: Active enrollment with guardian information
v_class_rosters: Complete class assignments and demographics
v_student_grades: Grade calculations with letter grade assignments
v_teacher_workload: Class assignments and student counts
v_financial_summary: Payment tracking and outstanding balances
🤝 Contributing
We welcome contributions to the Luminosity project! Here's how to get involved:

Development Setup
bash
# Fork the repository
git clone https://github.com/yourusername/luminosity.git
cd luminosity

# Create feature branch
git checkout -b feature/your-feature-name

# Set up development environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# Run validation tests
python scripts/validate_decade_data.py --test-mode
Contribution Guidelines
Data Quality: All generated data must pass validation tests
Documentation: Update relevant docs for new features
Testing: Include unit tests for new functionality
Performance: Consider impact on large dataset operations
Backwards Compatibility: Maintain existing API contracts
Areas for Contribution
🎨 Data Visualization: Streamlit dashboards and analytical tools
🤖 Machine Learning: Predictive models and analysis algorithms
📊 Reporting: Enhanced analytics and report generation
🌐 API Development: RESTful services and GraphQL endpoints
📚 Documentation: Tutorials, examples, and best practices
📜 License
This project is licensed under the MIT License - see the LICENSE file for details.

Usage Rights
✅ Commercial Use: Use in proprietary software and commercial applications
✅ Modification: Adapt and extend for your specific needs
✅ Distribution: Share with attribution to original authors
✅ Private Use: Internal organizational usage without restrictions

Attribution
If you use Luminosity in research or publications, please cite:

bibtex
@dataset{luminosity2024,
  title={Luminosity School Management System: A Comprehensive Synthetic Educational Dataset},
  author={Lumenlytics Team},
  year={2024},
  url={https://github.com/lumenlytics/luminosity},
  note={10-year longitudinal school data with 650K+ grade records}
}
📞 Support & Community
Getting Help
📖 Documentation: Comprehensive guides in /docs directory
🐛 Issue Tracker: GitHub Issues
💬 Discussions: GitHub Discussions
📧 Email Support: luminosity@lumenlytics.com
Community Resources
🎓 Educational Research Group: Connect with researchers using Luminosity
💻 Developer Community: Share tools and extensions
📊 Data Science Forum: Discuss analytical approaches and findings
🏫 School Admin Network: Real-world implementation experiences
🔮 Future Roadmap
Planned Enhancements
📅 2024 Q4

Interactive Streamlit dashboard for data exploration
Advanced ML models for student outcome prediction
Real-time data generation APIs
📅 2025 Q1

Integration with popular school management systems
Enhanced curriculum mapping and standards alignment
Multi-language support for international schools
📅 2025 Q2

Blockchain integration for academic credential verification
AI-powered recommendation engine for student interventions
Mobile application for guardian and student access
Long-term Vision
Transform Luminosity into the gold standard for educational data simulation, supporting:

🌍 Global Education Research: Multi-cultural and international school modeling
🏛️ Policy Development: Government and institutional decision support
🎯 Personalized Learning: AI-driven individual student pathway optimization
🔬 Evidence-Based Practice: Data-driven educational methodology validation
🙏 Acknowledgments
Special thanks to the educational community and open-source contributors who made this project possible:

Educational Researchers who provided real-world insights and validation
School Administrators who shared operational knowledge and best practices
Data Science Community for analytical frameworks and methodologies
Open Source Contributors for libraries, tools, and collaborative development
Built with ❤️ by the Lumenlytics Team for the advancement of educational technology and research.

<div align="center">
⭐ If you find Luminosity useful, please give us a star on GitHub! ⭐

🌟 Star this project on GitHub 🌟

</div>
