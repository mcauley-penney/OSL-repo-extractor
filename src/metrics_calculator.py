"""
This module is a storehouse for tools that derive social metrics from data
gathered from GitHub via the Extractor class.
"""

from src import conf, dict_utils, file_io_utils, schema


def get_social_metrics_data(user_cfg: conf.Cfg):
    """
    TODO:
        • finish doc

    Top-level access point for gathering social metrics data.

    :param issue_json:
    :type issue_json:
    """

    issue_json_path = user_cfg.get_cfg_val("issue_output_file")
    issue_dict = file_io_utils.read_jsonfile_into_dict(issue_json_path)
    issue_metrics_dict = {}

    if len(issue_dict) > 0:
        for num, issue in issue_dict.items():

            cmmnt_dict = issue["issue_comments"]

            cur_metrics_dict = {
                num: schema.get_item_data(user_cfg, "social_metrics", cmmnt_dict)
            }

            cur_metrics_dict[num]["num_comments"] = issue["num_comments"]

            issue_metrics_dict = dict_utils.merge_dicts(
                issue_metrics_dict, cur_metrics_dict
            )

        out_dir = user_cfg.get_cfg_val("output_dir")

        # lop repo str off of full repo info, e.g. owner/repo
        repo_title = user_cfg.get_cfg_val("repo").rsplit("/", 1)[1]

        out_path = file_io_utils.mk_json_outpath(out_dir, repo_title, "metrics")

        file_io_utils.write_merged_dict_to_jsonfile(issue_metrics_dict, out_path)

    else:
        print(f'{" " * 4}No valid issue JSON at "{issue_json_path}"')

    return 0
