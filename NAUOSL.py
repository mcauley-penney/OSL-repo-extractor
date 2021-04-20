from flatten_json import flatten
import json
import requests
import csv
import sys

def main():

    owner = "StuckInsideJake"
    repo = "EricAndreDiscordBot"
    token = ""
    jsonWriter = open("jsonData.csv", "w")

    getIssueData(owner, repo, jsonWriter)





def getIssueData(owner, repo, jsonFile):

    baseUrl = "https://api.github.com/"
    repos = "repos"
    issues = "issues"
    issueApi = "repos/%s/%s/issues"%(owner,repo)

    request = requests.get(baseUrl+issueApi).json()

    requestData = json.dumps(request[0])


    jsonFile.write(requestData)






if __name__ == "__main__":
    main()
