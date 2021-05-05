from github import Github
import csv

#api
git = Github("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")
# repos to mined
repoList = ["Facebook/react","StuckInsideJake/386_Team_7","JabRef/jabref","StuckInsideJake/EricAndreDiscordBot"]
repo = git.get_repo(repoList[0])

# pull request related apis
pr = repo.get_pulls()
pulls = repo.get_pulls(state='open', sort='created', base='master')

# issue related apis
issue = repo.get_issues()
issues = repo.get_issues(state="closed")

#complete list
data = []

#Pull request related lists
prNumL = []

#Issue related lists
issueClosedDates = []
issueAuthors = []
issueTitles = []
issueBodies = []
isssueComments = []

#Commit related lists

def main():
   #
    with open("github.csv", "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_NONE, delimiter='|', quotechar='', escapechar='\\')
        descriptors = "PR_Number,Issue_Closed_Date, Issue_Author, Issue_Title, Issue_Body, Issue_comments, PR_Closed_Date,PR_Author, PR_Title, PR_Body, PR_Comments, Commit_Author, Commit_Date, Commit_Message, isPR"
        cont_pulls = 0
        cont_issues = 0

        # sets up the table
        writer.writerow([descriptors])

        prNumL = getPRNumber()
        issueClosedDates = getIssueClosedDate()
        issueAuthors = getIssueAuthor()
        issueTitles = getIssueTitle()
        issueBodies = getIssueBody()


        data = [prNumL, issueClosedDates,issueAuthors, issueTitles, issueBodies]
        writer.writerows(data)




        csvfile.close()

   #

def getPRNumber():
    #
    outList = []

    for pr in pulls:
       #comments = pr.get_issue_comments()
       #for each_comment in comments:
           #assert isinstance(each_comment.user.login, object)
       ftitle = ''
       #title = each_comment.user.login
       #print ('Comment: ', title[0:5], '...')
       print(pr.number)
       prStr = str(pr.number) + "," + ftitle
       print(prStr)
       outList.append(prStr)
    return outList
   #

def getIssueClosedDate():
    #
    outList = []

    for issue in issues:
        issueDateStr = str(issue.closed_at)
        print(issueDateStr)
        outList.append(issueDateStr)
    return outList
    #

def getIssueAuthor():
    #
    outList = []

    for issue in issues:
        issueAuthorStr = str(issue.user.name)
        print(issueAuthorStr)
        outList.append(issueAuthorStr)
    return outList
    #

def getIssueTitle():
    #
    outList = []
    index = 0

    for issue in issues:
        issueTitleStr = str(issue.title)
        print("Getting issue title at index: "+str(index))
        index+=1
        outList.append(issueTitleStr)
    return outList
    #


def getIssueBody():
    #
    outList = []
    index = 0

    for issue in issues:
        issueBodyStr = str(issue.body)
        print("getting body at index:" + str(index))
        index+=1
        outList.append(issueBodyStr)
    return outList
    #
def getIssueComments():
    #
    outList = []
    index = 0

    for issue in issues:
        issueCommentStr = str(issue.comments)
        print("getting comments at index:"+str(index))
        index+=1
        outList.append(issueCommentStr)

    return outList
    #








if __name__ == '__main__':
    main()
