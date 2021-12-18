#### Timeline
[2021](#2021)

- [December](#2021-12)
---


### 2021
---
#### 2021-12

2021-12-12

- command pattern caller dispatch tables via dictionaries
    - begin transition from lambda to function objects
        - allows us to continue to not provide params at the time of instantiation
    - condense like API calls in dict and allow for functions to accept any type of object
        - example: PR and Issue objects both have numbers accessed in the same way, x.num
- use generator expression instead of list comprehension in `__get_issue_comments`

<br>
2021-12-14

- command pattern caller dispatch tables via dictionaries
    - remove all lambdas from commit dispatch dict
    - create top-level commit info getter, `get_commit_data()`
        - create getters for commit info, e.g. `get_commit_files()`

<br>
2021-12-15

- init JSON writing functionality
    - See `Writer` class
    - ability to recursively update nested dictionaries in JSON output
        - further testing is needed but works as of right now

<br>
2021-12-16

- move API getters, dispatch tables, and `CFG_SCHEMA` into `Extractor`
    - requires adding `self` param to all dict comprehension dispatch function calls
- remove all functions from utils and rightfully place in `Extractor`
- init docs dir and begin documentation
- add documentation in `Extractor`

<br>
2021-12-17

- combine PR and commit getters, for now
    - can still get only commit info by simply not providing fields to "pr_fields" cfg
- remove option to send output to different places
    - default to same location
- init using range to find API object numbers instead of using it as indices for paginated lists
    - allows user to target specific API object in paginated list of arbitrary length and get its data
