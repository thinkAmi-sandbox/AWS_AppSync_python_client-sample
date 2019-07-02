from graphqlclient import GraphQLClient

from secret import API_KEY, API_URL


def execute_query_api(gql_client):
    # ham Queryの実行
    ham = """
        query {
          ham(req: "456") {
            field
            event
            context
          }
        }
    """
    ham_result = gql_client.execute(ham)
    print(ham_result)
    # => {"data":
    # {"ham":{
    #  "field":"from_ham",
    #  "event":"{\"field\":\"from_ham\",\"args\":{\"req\":\"456\"}}",
    #  "context":"{\"callbackWaitsForEmptyEventLoop\":true,
    #              \"functionVersion\":\"$LATEST\",
    #              \"functionName\":\"AppSyncDatasource\",
    #              \"memoryLimitInMB\":\"128\",
    #              \"logGroupName\":\"/aws/lambda/AppSyncDatasource\",
    #              \"logStreamName\":\"2019/07/xx/[$LATEST]xxx\",
    #              \"invokedFunctionArn\":\"arn:aws:lambda:region:iam:function:AppSyncDatasource\",
    #              \"awsRequestId\":\"xx-xx-xx-xx-xx\"}"}}}

    # spam Queryの実行
    spam = """
        query {
          spam(req: "789") {
            field
            event
            context
          }
        }
    """
    spam_result = gql_client.execute(spam)
    print(spam_result)
    # => {"data":
    # {"spam":{
    #  "field":"from_spam",
    #  "event":"{\"field\":\"from_spam\",\"args\":{\"req\":\"789\"}}",
    #  "context":"{\"callbackWaitsForEmptyEventLoop\":true,
    #              \"functionVersion\":\"$LATEST\",
    #              \"functionName\":\"AppSyncDatasource\",
    #              \"memoryLimitInMB\":\"128\",
    #              \"logGroupName\":\"/aws/lambda/AppSyncDatasource\",
    #              \"logStreamName\":\"2019/07/xx/[$LATEST]xxx\",
    #              \"invokedFunctionArn\":\"arn:aws:lambda:region:iam:function:AppSyncDatasource\",
    #              \"awsRequestId\":\"xx-xx-xx-xx-xx\"}"}}}


if __name__ == '__main__':
    c = GraphQLClient(API_URL)
    c.inject_token(API_KEY, 'X-Api-Key')
    execute_query_api(c)
