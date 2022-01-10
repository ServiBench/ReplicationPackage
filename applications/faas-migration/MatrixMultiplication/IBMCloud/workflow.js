const composer = require("openwhisk-composer");

module.exports = composer.seq(
    "create-matrix",
    composer.if(
        composer.action("choose-type", {
            action: function (data) {
                data.value = data.size >= 10;
                console.log(JSON.stringify(data));
                return data;
            }
        }),
        composer.seq(
            composer.action("set-worker-count", {
                action: function (data) {
                    data.worker_count = 5;
                    return data;
                }
            }),
            "distribute-work",
            composer.parallel(
                composer.seq(
                    composer.action("set-worker-id-0", {
                        action: function (data) {
                            data.worker_id = 0;
                            return data;
                        }
                    }),
                    "parallel-worker"
                ),
                composer.seq(
                    composer.action("set-worker-id-1", {
                        action: function (data) {
                            data.worker_id = 1;
                            return data;
                        }
                    }),
                    "parallel-worker"
                ),
                composer.seq(
                    composer.action("set-worker-id-2", {
                        action: function (data) {
                            data.worker_id = 2;
                            return data;
                        }
                    }),
                    "parallel-worker"
                ),
                composer.seq(
                    composer.action("set-worker-id-3", {
                        action: function (data) {
                            data.worker_id = 3;
                            return data;
                        }
                    }),
                    "parallel-worker"
                ),
                composer.seq(
                    composer.action("set-worker-id-4", {
                        action: function (data) {
                            data.worker_id = 4;
                            return data;
                        }
                    }),
                    "parallel-worker"
                )
            ),
            composer.action("cleanup-context", {
                action: function (data) {
                    console.log(JSON.stringify(data));
                    let context = data.value[0];
                    context.worker_id = null;
                    console.log(JSON.stringify(context));
                    return context;
                }
            }),
            "build-result"
        ),
        composer.seq(
            composer.action("zero-out-worker-count", {
                action: function (data) {
                    data.worker_count = 5;
                    return data;
                }
            }),
            "serial-multiply"
        )
    ),
    "generate-report"
);