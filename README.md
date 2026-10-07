# NET2008 DevOps: course repository

Course material for NET2008 DevOps (Algonquin College). You have the option to work in **GitHub Codespaces**: GitHub gives you a Linux computer in your web browser with Python, Git and the GitHub command line already installed. You install nothing, and it works the same on Windows, macOS and Linux.

## Schedule and materials

| Week | Topic | Materials | Assessment |
|---|---|---|---|
| 1 | Holiday: no class | | |
| 2 | Course Review | [Lecture](week02/W02_Lecture.pptx), [Lab](week02/W02_Lab_EnvironmentSetup.ipynb) | Lab: Notebook and Python Setup (1%) |
| 3 | Python Review | [Lecture](week03/W03_Lecture_PythonFundamentals.ipynb), [Lab](week03/W03_Lab_PythonFundamentals.ipynb) | Lab: Python (1%) |
| 4 | Python Review | [Lecture](week04/W04_Lecture_PythonReview_Part2.ipynb), [Lab](week04/W04_Lab_PythonFundamentals_Part2.ipynb) | Lab: Python (1%) |
| 5 | APIs and Data Formats | [Lecture](week05/W05_Lecture_APIs_DataFormats.ipynb), [Lab](week05/W05_Lab_APIs_DataFormats.ipynb) | Lab: API (1%), [Practical Assessment 1](week05/pa1/PA1_Project_Brief.pdf) (5%) |
| 6 | Version Control | [Lecture](week06/W06_Lecture_GitAndGitHub.md) | Lab: Git/GitHub (2%) |
| 7 | Containers, Mid-term Review | | Lab: Docker Containers (2%) |
| 8 | Mid-term | | Practical Assessment 2: Containerized Python App (5%) |
| 9 | Study Break | | |
| 10 | Container Orchestration | | Lab: Kubernetes (2%) |
| 11 | Virtualization and IaC | | Lab: VMs, Vagrant and Terraform (2%) |
| 12 | IaC Cont.: Ansible | | Lab: Ansible (2%), Practical Assessment 3: Containerized Infrastructure Pipeline (5%) |
| 13 | CI/CD | | Lab: GitHub Actions and Jenkins (3%) |
| 14 | Monitoring and Exam Review | | Lab: Nagios, Splunk, Zabbix and ELK (3%) |
| 15 | Final | | Practical Assessment 4: Pipeline Incident Audit |

Course information and the full curriculum are in [course-info](course-info/).

Materials for a week appear here when that week starts. The schedule can change, and Brightspace is the final source for due dates.

## Open a Codespace (first time)

1. Sign in at <https://github.com>.
2. On this page, click the green **<> Code** button, open the **Codespaces** tab, and click **Create codespace on main**.
3. Wait one to two minutes. A browser tab opens with a code editor and a terminal at the bottom.
4. Open the material for your week from the file list on the left and follow it. Notebooks (`.ipynb`) open in the editor and run with the Python kernel that is already installed.

Next time, go to <https://github.com/codespaces> and click your Codespace. When you finish, click the three dots next to it and choose **Stop codespace**.

To get new weeks into an existing Codespace, run `git pull` in its terminal.
