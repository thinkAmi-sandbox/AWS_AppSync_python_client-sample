import json
from urllib.parse import urlparse

from graphqlclient import GraphQLClient
from paho.mqtt.client import Client as MQTTClient

from secret import API_KEY, API_URL


def execute_query_api(gql_client):
    query = """
        query listAppSyncToDos {
          listAppSyncToDos {
            items {
              title
              content
            }
          }
        }
    """
    result = gql_client.execute(query)
    print(result)
    # => {"data":{"listAppSyncToDos":{"items":[{"title":"title1","content":"content1"}]}}}


def execute_mutation_api(gql_client, title, content):
    # AWS AppSyncのQueriesをそのまま貼って動作する
    mutation = """
        mutation createAppSyncToDo($createappsynctodoinput: CreateAppSyncToDoInput!) {
            createAppSyncToDo(input: $createappsynctodoinput) {
                title
                content
              }
            }
    """

    variables = {
        "createappsynctodoinput": {
            "title": title,
            "content": content,
        }
    }

    result = gql_client.execute(mutation, variables=variables)
    print(result)
    # => {"data":{"createAppSyncToDo":{"title":"title1","content":"content1"}}}


def execute_subscription_api(gql_client, subscription):
    """ subscription のため、以下の処理を行う

        1. Subscription APIへ投げる
        2. 1.のレスポンスに含まれる内容を使って、エンドポイントにMQTTで接続する

        参考：https://github.com/eclipse/paho.mqtt.python/issues/277
    """

    def on_connect(client, userdata, flags, respons_code):
        print('connected')
        # 接続できたのでsubscribeする
        client.subscribe(topic)

    def on_message(client, userdata, msg):
        # メッセージを表示する
        print(f'{msg.topic} {str(msg.payload)}')
        # onCreate系
        # path/to/onCreateAppSyncToDo/ b'{"data":{"onCreateAppSyncToDo":{"title":"new","content":"new content","__typename":"AppSyncToDo"}}}'
        #
        # onUpdate系
        # path/to/onUpdateAppSyncToDo/ b'{"data":{"onUpdateAppSyncToDo":{"title":"new","content":"update","__typename":"AppSyncToDo"}}}'
        #
        # onDelete系
        # path/to/onDeleteAppSyncToDo/ b'{"data":{"onDeleteAppSyncToDo":{"title":"new","content":"update","__typename":"AppSyncToDo"}}}'

        # メッセージを受信したので、今回は切断してみる
        # これがないと、再びメッセージを待ち続ける
        client.disconnect()

    # Subscription APIに投げると、MQTTの接続情報が返ってくる
    r = gql_client.execute(subscription)

    # JSON文字列なので、デシリアライズしてPythonオブジェクトにする
    response = json.loads(r)

    # 中身を見てみる
    print(response)
    """ =>
    {'extensions': 
         {'subscription':
              {
                  'mqttConnections': [
                      {'url': 'wss://<host>.iot.<region>.amazonaws.com/mqtt?<v4_credential>',
                       'topics': ['path/to/onCreateAppSyncToDo/'], 
                       'client': '<client_id>'}],
                  'newSubscriptions': {
                      'onCreateAppSyncToDo': 
                          {'topic': 'path/to/onCreateAppSyncToDo/', 
                           'expireTime': None}}}}, 
        'data': {'onCreateAppSyncToDo': None}}
    """

    # Subscribeするのに必要な情報を取得する
    client_id = response['extensions']['subscription']['mqttConnections'][0]['client']
    topic = response['extensions']['subscription']['mqttConnections'][0]['topics'][0]

    # URLはparseして、扱いやすくする
    url = response['extensions']['subscription']['mqttConnections'][0]['url']
    urlparts = urlparse(url)

    # ヘッダーとして、netloc(ネットワーク上の位置)を設定
    headers = {
        'Host': '{0:s}'.format(urlparts.netloc),
    }

    # 送信時、ClientIDを指定した上でWebSocketで送信しないと、通信できないので注意
    mqtt_client = MQTTClient(client_id=client_id, transport='websockets')

    # 接続時のコールバックメソッドを登録する
    mqtt_client.on_connect = on_connect

    # データ受信時のコールバックメソッドを登録する
    mqtt_client.on_message = on_message

    # ヘッダやパスを指定する
    mqtt_client.ws_set_options(path=f'{urlparts.path}?{urlparts.query}',
                               headers=headers)

    # TLSを有効にする
    mqtt_client.tls_set()

    # wssで接続するため、443ポートに投げる
    mqtt_client.connect(urlparts.netloc, port=443)

    # 受信するのを待つ
    mqtt_client.loop_forever()


if __name__ == '__main__':
    c = GraphQLClient(API_URL)
    c.inject_token(API_KEY, 'X-Api-Key')

    # 登録する
    execute_mutation_api(c, 'ham', 'spam')

    # 登録した情報を取得する
    execute_query_api(c)

    # DynamoDBが更新された時の通知を1回だけ受け取る
    # Subscription API用のGraphQL (onCreate系)
    create_subscription = """
        subscription {
            onCreateAppSyncToDo {
                title
                content
            }
        }
    """
    execute_subscription_api(c, create_subscription)

    # ↑の実行後に、AppSyncのQueriesから、登録処理を行う(以下はその結果例)
    # {
    #     "data": {
    #         "createAppSyncToDo": {
    #             "title": "new",
    #             "content": "new content"
    #         }
    #     }
    # }

    # Subscription API用のGraphQL (onCreate系)
    update_subscription = """
        subscription {
            onUpdateAppSyncToDo {
                title
                content
            }
        }
    """
    execute_subscription_api(c, update_subscription)

    # ↑の実行後に、AppSyncのQueriesに以下を追加する
    # mutation updateAppSyncToDo($updateappsynctodoinput: UpdateAppSyncToDoInput!) {
    #     updateAppSyncToDo(input: $updateappsynctodoinput) {
    #         title
    #         content
    # }
    #
    # また、QUERY VARIABLESも変更する
    # {
    #     "updateappsynctodoinput": {
    #         "title": "new",
    #         "content": "update"
    #     }
    # }
    #
    # その後、AppSyncコンソールで実行し、以下の結果を得る
    # {
    #     "data": {
    #         "updateAppSyncToDo": {
    #             "title": "new",
    #             "content": "update"
    #         }
    #     }
    # }

    delete_subscription = """
        subscription {
            onDeleteAppSyncToDo {
                title
                content
            }
        }
    """
    execute_subscription_api(c, delete_subscription)

    # ↑の実行後に、AppSyncのQueriesに以下を追加する
    # mutation deleteAppSyncToDo($deleteappsynctodoinput: DeleteAppSyncToDoInput!) {
    #     deleteAppSyncToDo(input: $deleteappsynctodoinput) {
    #     title
    # content
    # }
    # }
    #
    # また、QUERY VARIABLESも変更する
    # {
    #     "deleteappsynctodoinput": {
    #         "title": "new"
    #     }
    # }
    #
    # その後、AppSyncコンソールで実行し、以下の結果を得る
    # {
    #     "data": {
    #         "deleteAppSyncToDo": {
    #             "title": "new",
    #             "content": "update"
    #         }
    #     }
    # }
