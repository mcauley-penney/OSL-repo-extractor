# COMMIT ACCESS POINT #
# def get_repo_commit_data(self) -> None:
#     """
#     Create a dict of contributors and their contributions.
#
#     The project is interested in determining the core contributors for a
#     given repository. To do this, we have implemented the algorithm
#     discussed in Coelho et al., 2018 (see citation below) wherein the
#     contributors whose sum commits are 80% of the total commits for the
#     repo are aggregated and those from that group who have less than five
#     commits are disregarded. This implementation is found in the OSL
#     metrics aggregator. This method creates a dict of all contributors,
#     descendingly ordered by total commits, for input into the Coelho et
#     al. custom "Commit-Based Heuristic" algorithm.
#
#     Citations:
#         Coelho J, Valente MT, Silva LL, Hora A (2018) Why we engage in
#         floss: Answers from core developers. In: Proceedings of the 11th
#         International Workshop on Cooperative and Human Aspects of
#         Software Engineering, pp 114–121
#
#         link: https://arxiv.org/pdf/1803.05741.pdf
#     """
#
#     def __get_dev_num_contribs(commits, total_num_commits: int, out_file: str):
#         """
#         TODO.
#
#         Args:
#             num_commits ():
#
#         Returns:
#             dict: sorted dictionary of (contributor: contributions) pairs
#         """
#         contrib_dict = {}
#         i = 0
#         print(f"{TAB * 2}total: {total_num_commits}")
#
#         while i < total_num_commits:
#             try:
#                 author = commits[i].commit.author.name
#
#                 if author not in contrib_dict:
#                     contrib_dict[author] = 1
#
#                 else:
#                     contrib_dict[author] += 1
#
#             except github.RateLimitExceededException:
#                 self.__update_output_json_for_sleep(contrib_dict, out_file)
#
#             else:
#                 print(f"{CLR}{TAB * 2}", end="")
#                 print(f"index: {i}, ", end="")
#                 print(f"calls: {self.gh_sesh.get_remaining_calls()}", end="\r")
#                 i += 1
#
#         print("\n")
#
#         return dict(sorted(contrib_dict.items(), key=lambda x: x[1], reverse=True))
#
#     contrib_opts: dict = self.cfg.cfg_dict["repo_data"]["by_commit"][
#         "dev_contributions"
#     ]
#
#     startdate: list = contrib_opts["start_date"]
#     interval: list = contrib_opts["interval"]
#     out_file: str = self.get_cfg_val("output_file")
#
#     start_tm: datetime.datetime = datetime.datetime(
#         startdate[0], startdate[1], startdate[2], 0, 0, 0
#     )
#
#     cur_entry = {}
#     data_dict = {}
#
#     # TODO:
#     #   - implement sanitization
#     #       - check date of lowest PR and only collect commits from there
#     #   - modularize, this is too lengthy
#     #   - fix printing
#
#     while start_tm < datetime.datetime.now():
#         try:
#             # get the current starting time plus the user-defined
#             # interval. This will be the end date of the current
#             # request for a paginated list of commits.
#             start_tm_next = start_tm + datetime.timedelta(
#                 weeks=interval[0], days=interval[1]
#             )
#
#             print(f"{TAB}{start_tm} - {start_tm_next}")
#
#             # get commits to process
#             cur_commit_list = self.__get_commits_paged_list(start_tm, start_tm_next)
#
#             total_commits = cur_commit_list.totalCount
#
#             cur_entry["num_commits"] = total_commits
#
#             # process commits
#             cur_entry["contributions"] = __get_dev_num_contribs(
#                 cur_commit_list, total_commits, out_file
#             )
#
#             # TODO: should use a subkey to specify end time, but how to
#             #       organize it? Nested keys make it dificult to work
#             #       with and aren't a great way of organizing for
#             #       our purposes. For example, when accessing this data
#             #       later, if we have multiple subkeys (end of interval)
#             #       under a key (start of interval), must have a way to
#             #       choose which end time we want to get core contribs
#             #       from.
#             cur_entry = {start_tm.strftime("%Y-%m-%dT%H:%M:%SZ"): cur_entry}
#
#             start_tm = start_tm_next
#
#         except github.RateLimitExceededException:
#             self.__update_output_json_for_sleep(data_dict, out_file)
#
#         else:
#             # merge it to the total dict
#             data_dict = dict_utils.merge_dicts(data_dict, cur_entry)
#             cur_entry.clear()
#
#     # nest commit data in appropriate label
#     data_dict = {"by_commit": data_dict}
#
#     file_io_utils.write_merged_dict_to_jsonfile(data_dict, out_file)

# def __get_commits_paged_list(self, start, end):
#     """
#     Retrieve and store a paginated list of commits from GitHub.
#
#     Raises:
#         github.RateLimitExceededException: if rate limited
#             by the GitHub REST API, sleep the program until
#             calls can be made again and continue attempt to
#             collect desired paginated list.
#
#         github.UnknownObjectException: this exception is
#             thrown at least when a repository is not
#             accessible. This is can occur because the repo
#             is private or does not exist, but may occur
#             for other, unforeseen reasons.
#
#     Returns:
#         github.PaginatedList of github.Commit.
#     """
#     while True:
#         try:
#             commits_paged_list = self.repo_obj.get_commits(since=start, until=end)
#
#         except github.RateLimitExceededException:
#             self.__sleep_extractor()
#
#         else:
#             return commits_paged_list


# SCHEMA
# "by_commit": {
#     "type": "dict",
#     "schema": {
#         "dev_contributions": {
#             "type": "dict",
#             "schema": {
#                 "start_date": {
#                     "type": "list",
#                     "items": [
#                         {"type": "integer", "min": 1999, "max": 2022},
#                         {"type": "integer", "min": 1, "max": 12},
#                         {"type": "integer", "min": 1, "max": 31},
#                     ],
#                 },
#                 "interval": {
#                     "type": "list",
#                     "items": [
#                         {"type": "integer", "min": 0, "meta": "weeks"},
#                         {
#                             "type": "integer",
#                             "min": 0,
#                             "max": 6,
#                             "meta": "days",
#                         },
#                     ],
#                 },
#             },
#         },
#     },
# },
