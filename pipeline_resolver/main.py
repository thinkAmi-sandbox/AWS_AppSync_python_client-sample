from graphqlclient import GraphQLClient

from secret import API_KEY, API_URL


def execute_query_api(gql_client):
    # pipeline resolverを使ったqueryを呼ぶ：データがある場合
    query = """
        query {
          getBlogWithAuthor(id: "1") {
            id
            title
            author_id
            author_name
          }
        }
    """
    result = gql_client.execute(query)
    print(result)
    # =>
    # {"data":{"getBlogWithAuthor":{"id":"1","title":"ham","author_id":"100","author_name":"foo"}}}

    # pipeline resolverを使ったqueryを呼ぶ：データがない場合
    query = """
        query {
          getBlogWithAuthor(id: "x") {
            id
            title
            author_id
            author_name
          }
        }
    """
    result = gql_client.execute(query)
    print(result)
    # =>
    # {
    # "data":{"getBlogWithAuthor":null},
    # "errors":[{"path":["getBlogWithAuthor"],
    #            "data":null,
    #            "errorType":"DynamoDB:AmazonDynamoDBException",
    #            "errorInfo":null,
    #            "locations":[{"line":3,"column":11,"sourceName":null}],
    #            "message":"The provided key element does not match the schema
    #                       (Service: AmazonDynamoDBv2; Status Code: 400;
    #                        Error Code: ValidationException;
    #                        Request ID: xxx)"}]}


if __name__ == '__main__':
    c = GraphQLClient(API_URL)
    c.inject_token(API_KEY, 'X-Api-Key')
    execute_query_api(c)
