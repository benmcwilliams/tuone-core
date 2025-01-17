The purpose of this obsidian vault is for users to manually check the outputs from the tuone model. The tuone model processes text from newspaper articles into structured investment information.

The user inputs information to correct any information in the "Properties" of a phase card. Once a phase card has been checked and the user is happy with it, checked should be set == True (ie tick the box). If it is determined that a phase should not exist, then the user should set reject-phase == True (ie tick the box). 

*Duplicates*
Update company dictionary
Update location dictionary
Update canonical nodes


Best way to validate is by first loading "company" view of a phase-ID to understand which projects are involved and whether duplicates (and potentially also location)
Then to load project-view to see each unique phase

projects components within a technology do not have to be mutually exclusive (for example hydrogen - fuel cell and also vehicle to arrive at fuel cell)