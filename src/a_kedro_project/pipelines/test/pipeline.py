from kedro.pipeline import Pipeline, node, pipeline


def as_is(x):
    print(x)
    return x


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=as_is,
                inputs="data1",
                outputs="out1",
                name="data1",
            ),
            node(
                func=as_is,
                inputs="data2",
                outputs="out2",
                name="data2",
            ),
            node(
                func=as_is,
                inputs="data3",
                outputs="out3",
                name="data3",
            ),
        ]
    )
