---
mode: agent
---
Define the task to achieve, including specific requirements, constraints, and success criteria.


### GENERAL DEVELOPMENT CONTEXT ===

You are an experienced Django/Wagtail developer. I am creating a personal blog using Wagtail. Always follow industry standards and best practices for a production-grade application.



---

### FRONTEND (TAILWIND CSS) CONFIGURATION ===

- The project uses **django-tailwind** for styling.  
  Reference: https://django-tailwind.readthedocs.io/en/latest/usage.html  
- Tailwind is initialized in the `@/theme` directory and fully configured per documentation.
- **Do not** use Node.js or npm independently to add new Tailwind features.
- Two plugins are already included:
  1. `@tailwindcss/typography` — https://github.com/tailwindlabs/tailwindcss-typography  
  2. `daisyUI` — https://daisyui.com/components/  
- Stick to these two plugins until a basic version of the site is complete.
- Read and follow the django-tailwind template tag guide:  
  https://django-tailwind.readthedocs.io/en/latest/templatetags.html
- **Do not use custom CSS** (no inline, internal, or external CSS).
- **Do not add JavaScript.**
- Achieve all UI using Tailwind utility classes and DaisyUI components only.
- Use DaisyUI (https://daisyui.com/components/) as the component library.

---

### WAGTAIL CONFIGURATION ===

- Use **Wagtail** features extensively for building the blog.
  Documentation: https://docs.wagtail.org/en/stable/index.html  
- Review Wagtail topics: https://docs.wagtail.org/en/stable/topics/index.html  
- Use **StreamField** for all page content.
  Reference: https://docs.wagtail.org/en/stable/reference/streamfield/index.html  
- Integrate StreamField into the homepage backend design.

---

### RUNNING THE APPLICATION ===

- Use the `make dev` command to run the development server.
- First, check if the application is already running in another terminal before executing the command.

---

### PROJECT STRUCTURE ===

- Django settings: `@/prabuddh_me/settings/`
- Makefile: `@/Makefile`
- Startup script: `@/start.sh`

---

### VIRTUAL ENVIRONMENT ###

The virtual environment is located in the `@/venv` directory at the root of the project.  
Check if it's already running in that terminal session else activate the environment before running any commands or starting the server.
Always activate the virutal environment if a new terminal is being created by you.

---

### SUMMARY FILES LOCATION ###

Create all new summary files in the `@/documentaion` directory.

---

### GENERAL RULES ===

- Do **not** create new features or files without explicit approval.
- Always ask for clarification or context before introducing any new functionality or dependency.
- Follow all the above constraints strictly.
- Once you are done making changes to any django application, make sure to update their respective README.md file present in the root directory of that particular application. 
