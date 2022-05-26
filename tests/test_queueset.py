from prompt_importer import importer


def test_keeps_size():
    q = importer.QueueSet(3)
    q.push("a")
    q.push("b")
    q.push("c")
    q.push("d")
    q.push("e")
    assert list(q) == ["e", "d", "c"]


def test_bumps_to_front():
    q = importer.QueueSet(4)
    q.push("a")
    q.push("b")
    q.push("a")

    assert list(q) == ["a", "b"]
