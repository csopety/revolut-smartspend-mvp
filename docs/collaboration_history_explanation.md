# Collaboration History Explanation

This project was built through human collaboration supported by AI tools and GitHub version control.

## Team Workflow

The starting point was an initial code version generated with ChatGPT by my teammate. We used that early version as a reference for planning the app layout and deciding which features should be included in the final MVP.

After that, we turned the planned feature instructions into Codex tasks. Codex then rebuilt and expanded the app from the ground up using my additional instructions, phase by phase.

## Roles

One teammate focused on testing, planning, and developing Codex prompts in a separate ChatGPT conversation. The other teammate worked directly with the Codex agent, passed in the agreed feature instructions, reviewed the implementation output, and asked Codex to run tests.

This created an iterative loop:

1. Discuss desired feature or UI change.
2. Convert the idea into a clear Codex instruction.
3. Let Codex implement the scoped change.
4. Run tests and compile checks.
5. Push the result through GitHub.
6. Let the teammate test the app from the repository.
7. Collect comments and convert them into the next Codex prompt.

## Human Feedback

After each step, my teammate tested the app and gave feedback. I then passed that feedback to Codex as implementation or correction instructions. This was especially important for UI flow, store routing, demo readiness, and making sure the app stayed understandable for the assignment.

## GitHub Version Control

GitHub was used as the project source of truth. We used commits, pushes, pulls, and branches to coordinate work and preserve history. This allowed one person to continue implementing with Codex while the other could test the current repository state and report issues.

The version control process helped us:

- keep a record of each development phase
- test changes after each iteration
- recover from mistakes if needed
- share the same project state
- prepare the final submission from a stable repository

## Why This Collaboration Model Worked

The workflow combined human planning with AI-assisted implementation. Human teammates decided what the MVP should prove, which features mattered, and whether the app worked in practice. Codex helped convert those decisions into working code, tests, and documentation.

This made the final project stronger because implementation, testing, prompt design, and product judgment happened as separate but connected activities.
