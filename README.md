# Sim

<p class="subtitle" markdown="1">discrete event simulation of software development</p>

> **2025-12-19:**
> This material is under active development.
> Feedback, suggestions, and corrections are very welcome,
> either as issues in [the GitHub repository][repo]
> or [by email](mailto:gvwilson@third-bit.com).

## Lessons

<div id="lessons" markdown="1">

1.  [Introduction](@/intro/): who this is for and what it covers.
1.  [Simple Simulations](@/simple/): the basics of discrete event simulation.
    -   A regular schedule with a single programmer.
    -   Introducing randomness.
    -   Monitoring and visualizing the simulation.
    -   Connecting a manager and a team of programmers with a job queue.
    -   Measuring throughput, delay, and utilization.
1.  [Teams](@/teams/): multiple actors and a little theory.
    -   The exponential and log-normal distributions.
    -   One manager with multiple programmers.
    -   Watching the backlog grow.
    -   Little's Law and average waiting times.
1.  [More Features](@/features/): more complex simulations.
    -   Handling jobs in strict priority order.
    -   Using priorities as weights.
    -   The effect of periodic triage.
1.  [Interruptions](@/interrupts/): the bane of our existence.
    -   Throwing work away when it is interrupted.
    -   Resuming interrupted work (buggy and correct versions).
1.  [Feedback](@/feedback/): what goes around, comes around
    -   Adding testers and another queue to create a three-layer simulation.
    -   Refactoring to use classes instead of naked generators.
    -   Comparing three scenarios for handling re-work.
1.  [Conclusion](@/finale/): where we've been and what comes next

</div>

##  Appendices

<div id="appendices" markdown="1">

1.  [Generators](@/generators/)
1.  [License](@/license/)
1.  [Code of Conduct](@/conduct/)
1.  [Contributing](@/contributing/)
1.  [Bibliography](@/bibliography/)
1.  [Glossary](@/glossary/)

</div>

## Acknowledgments {: #acknowledgments}

-   [*Greg Wilson*][wilson-greg] is a programmer, author, and educator based in Toronto.
    He was the co-founder and first Executive Director of Software Carpentry
    and received ACM SIGSOFT's Influential Educator Award in 2020.

[repo]: https://github.com/gvwilson/sim/
[simpy]: https://simpy.readthedocs.io/
[wilson-greg]: https://third-bit.com/
