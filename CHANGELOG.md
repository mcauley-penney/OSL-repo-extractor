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
