exports.handler = (event, context, callback) => {
    // callback関数を使って、レスポンスを返す
    // 今回は、eventとcontextの値を返してみる
    callback(null, {
        "field": event.field,
        "event": JSON.stringify(event, 3),
        "context": JSON.stringify(context, 3),
    });
};
