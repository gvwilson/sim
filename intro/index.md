# Introduction

<p id="terms"></p>

-   [Discrete event simulation](g:des) models a system as a series of events,
    each of which occurs at a particular instant in time
    -   Don't advance a clock one tick at a time
    -   Instead,
        have each [process](g:process) say when it is next going to do something
        and jump ahead to the next interesting moment
-   This tutorial uses [SimPy][simpy] to model a software development team
    -   And to illustrate how hard it is to collect and interpret useful data

<div class="callout" markdown="1">

-   DES refers to active entities as processes
-   These are *not* the same as operating system processes (or threads)
-   Terminology can be confusing, but we're stuck with it

</div>

## Interesting Questions

-   Many proposals for tracking software development teams
    -   E.g., [DORA metrics][dora]
-   We'll build up to some simple ones:
    -   [Backlog](g:backlog): how much work is waiting to start over time?
    -   [Delay](g:delay): how long from job creation to job start?
    -   [Throughput](g:throughput): how many jobs are completed per unit time?
    -   [Utilization](g:utilization): how busy are the people on the team?
-   **Candidates to be included here: WIP in relation to both Delay and Throughput, Cycle time, Burn down chart / Burn up chart, Cummulative Flow Diagrama (CFD), interdependencies between tasks**

## Learner Profile

-   Shae, 20, is starting the third year of an undergraduate degree in computer science
    after doing a one-semester work placement at a local mobile application development company.
    - **What is typical for a third year undergraduate student in US and Canada? What is expected to be a foundational knowledge?**
-   Shae is comfortable with object-oriented programming in Python,
    and did well in their introductory courses on databases and web programming.
    They like working on homework assignments with friends,
    but had a bad experience in the team project in the web programming class.
    They use VS Code and Claude,
    but still mostly debug with print statements.
-   Shae found their work placement exciting because they got to work on real problems,
    but bewildering because they felt they spent more time in meetings than they did doing "real" work.
    They also heard senior programmers arguing about whether AI is a boon or a curse,
    and would like to know how to answer questions like that.
-   Shae is impatient with abstract theory;
    they learn best when generalizing from practical examples.

> This tutorial teaches Shae how to think analytically about software development processes,
> how to model and analyze those processes,
> and how to distinguish evidence-based claims from plausible punditry.
