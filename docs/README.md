# OSL Repo Extractor
## Introduction
The OSL Repo Extractor ("extractor") is a tool used to mine GitHub repositories for information relevant to the total OSL project under the supervision and direction of [Dr. Marco Gerosa](https://www.ime.usp.br/~gerosa/career.html). It is the first stage of the pipeline of the project, providing the pipeline the data that it requires.


## Context and Purpose
The goal of the OSL project is to predict the skills required by developers to successfully solve open issues on GitHub and label those issues accordingly. For example, if a particular issue requires that a developer have skill with databases, this project would like to discern that fact and label the issue accordingly. The intent is to make it easier for open source projects to get and retain contributors and for contributors to have an easier time making contributions.

The project aims to accomplish this goal by gathering data from issues that have been solved in the past, analyzing the libraries used in the commits which contributed to solving those issues, and applying that information to issues that have not yet been solved. This means the project is interested in three overarching types of data from GitHub: issues that have been solved and closed, the pull requests that contributed to solving them (meaning accepted and closed pull requests), and issues that are still open. Inside of those fields there are obviously subfields of data that are pertinent and useful. The extractor intends to gather all of this data for the rest of the project.


## To Future Contributors
The below authors are maintaining or have maintained this tool. If you have any questions or needs, please contact them.

1. Jacob Penney <jacobmpenney@gmail.com>
