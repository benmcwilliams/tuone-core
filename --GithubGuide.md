**Github logic**

1) to initiate a new branch
```bash
git checkout main #ensure you are in the main branch
git pull origin main   #ensure you are up to date with the remote repository
git checkout -b new-branch-name #create a new branch
```

```bash
year-month-day-username-purpose
```

2) to stage changes
```bash
git add <file-name> # Add a specific file
git add . # Add all modified files in the current directory
git add folder-name/   # Add all changes in a specific folder
```

3) to commit changes
```bash
git commit -m "Commit message"
```

4) to push changes
```bash
 git push origin new-branch-name
 ```

 5) to clean branches
 ``` bash
git checkout main #go back to the main branch
git branch -d new-branch-name #delete the branch you were working on
```



**Every time you start working - create a branch**
Always create your new branch from the correct base, usually the main  branch, unless you are specifically branching from another branch for a particular reason.

```bash
git checkout main # Check ou from the main branch
git pull origin main   # Ensure your main branch is up to date
git checkout -b new-branch-name # Create the new branch
```

In this repository, branches should be named as follows : 
```bash
year-month-day-username-purpose
```

Here are some common naming conventions for the purpose :
- feature: for new features 
- bugfix: for fixing bugs 
- chore: for non-functional tasks like documentation 
- validation: for validation of data in obsidian vault

Here is an example of a new branch name that follows this model :
 ```bash
2024-09-12-mjuge-chore
```

Once you have made changes to the files in the new branch, you need to commit them. Add only the files or folders you have changed. For example, if you are working on a folder called scripts, only update files within scripts/.

```bash
git add <file-name> # Add a specific file
git add . # Add all modified files in the current directory
git add folder-name/   # Add all changes in a specific folder
```

These commands add changes (new files, modified files, or deleted files) to the staging area. The staging area is where you prepare changes before committing them.

Always check your changes before committing. To ensure that you are only adding the intended files, you can use:

```bash
git status 
```
Make frequent commits with clear, descriptive messages. This helps track changes and makes the history easier to follow:

```bash
git commit -m "Commit message"
```
This command commits changes to the local repository, along with a message describing the changes. An effective commit message is essential for maintaining a clear and understandable project history, which makes collaboration easier and more efficient. Explain why the change was made, and how the problem was solved. Explain how the changes affect the system or relate to other code. A commit should solve a problem or introduce a change. Don't lump several unrelated changes into a single commit.

After you have committed your changes locally and you want to share your work with others on the remote repository: 

```bash
 git push origin new-branch-name
 ```

This command uploads your local commits to the remote repository (e.g., GitHub). This makes your changes available to others working on the project. 

After you have pushed your changes, you want them reviewed, this is the "**Pull Requests**": 

  1. On GitHub, go to the **Pull requests** tab of your repository.
   2. Click on a pull request to review it, discuss the changes, and merge it if everything is in order and the permission is given by the team.

A pull request is a way to propose changes in a project hosted on GitHub. It allows you to merge changes from your branch into another branch after a code or data review.

Don’t let your branches diverge too far from the base branch for a long time. Small, frequent (daily) pull requests are easier to review and less likely to result in conflicts.

Once the pulling request has been accepted and therefore the new branch has been merged into the main branch delete the branch to keep the repository clean:

``` bash
git checkout main #go back to the main branch
git branch -d new-branch-name #delete the branch you were working on
```

