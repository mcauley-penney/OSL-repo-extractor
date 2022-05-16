Author: Jacob McAuley Penney <jacobmpenney@gmail.com>


### Introduction
The purpose of this document is to serve as an introduction to this program in the context of the parent project and to act as an entryway for those who may be contributing or maintaining it in the future. Accordingly, it provides a discussion of its purpose and general structure. Before contacting the author with questions, please read and understand the contents below.

The OSL Repo Extractor ("extractor") is a tool used to mine GitHub repositories for information relevant to the total OSL project led by Fabio Marcos De Abreau Santos and under the supervision and direction of [Dr. Marco Gerosa](https://www.ime.usp.br/~gerosa/career.html). It is the first stage of the pipeline of the project, feeding the rest of it the data that it needs.


### Context and Purpose
The goal of the OSL project is to create predictive labels which discuss the skills required by developers to successfully solve open issues on GitHub. For example, if a particular issue requires that a developer have skill with a particular API, this project would like to discern that fact and label the issue accordingly. The intent is to make it easier for open source projects to get and retain contributors and for contributors to have an easier time contributing.

The project aims to do this by gathering data from issues that have been solved in the past, analyzing the libraries used in the commits which contributed to solving those issues, and applying that information to issues that have not yet been solved. This means the project is interested in three overarching types of data from GitHub: issues that have been solved and closed, the pull requests that contributed to solving them (meaning accepted and closed pull requests), and issues that are still open. Inside of those fields there are obviously subfields of data that are pertinent and useful. The extractor gathers all of this data for the rest of the project.


### Structure
The extractor employs singleton-like (soon to be properly singleton) classes which hold the various items needed to gather the data that we're after. In order, as of the time of this writing, one must initialize a configuration object and pass it to the extractor, which uses it to initialize a connection to GitHub and as a set of instructions on what pieces of data to gather.

[GitHub considers all pull requests as issues](https://docs.github.com/en/rest/issues/issues#list-issues-assigned-to-the-authenticated-user=). Given the three types of data that the project is interested in mentioned above, all data that the extractor is after can be gathered through a repository's list of issues.

To gather this data, the extractor employs [PyGithub](https://github.com/PyGithub/PyGithub) as a means of expediently interfacing with the GitHub REST API. The extractor is built around PyGithub's functionality


#### Future Improvements

- enforce singleton pattern for the configuration and GitHub session classes
    - They are intended to be singletons but there is currently no mechanism to enforce that only a single instance may be created.

- implement a class to manage the various external connections, including the GitHub session but possibly also to Postgres
    - As of right now, the GitHub session is the only one necessary, but that may change in the future and this proposed session manager class would be a more fitting "main actor" than the extractor class. The extractor class would become more lower level than the GitHub session instance.

- use class and function decorators to improve coherence
    - for example, this project has some methods that really should belong to a class but were left out of that class because they did not require an instance of the object type. These methods could benefit from the `@static` decorator
