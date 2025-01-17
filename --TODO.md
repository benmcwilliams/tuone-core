#next-action

- fix scraper for Power Technology
- add logic to drop projects where company_master == 'ignore' from v-unique-projects.py
- add feedback logic from obsidian, reject-phase to v-unique-projects.py
    
- consider whether phase level duplication option is necessary

dataviews structure 
- a folder **to-review** contains all the projects that need to be reviewed (filtered by technology)
- a folder **reviewed** contains all the projects that have been reviewed (filtered by technology)
- a dataview **finetune** contains all the projects that are being used to finetune the model
- a dataview **companies** lists all the companies in the database (different data; technologies involved; number of projects; project_locations)

#someday-maybe
- add processed projects logic to obsidian-sync.ipynb (depends how we want model to interact with validation in obsidian)
- add checker prompts
- determine whether/how to finetune model 
- look into batch processing through OpenAI server
- add 'fresh model' ability to obsidian-sync.ipynb (to replace all validated-variables with the new model-outputs). 
- clean phase-level prompt series into a separate function outside of main node-extraction.py


